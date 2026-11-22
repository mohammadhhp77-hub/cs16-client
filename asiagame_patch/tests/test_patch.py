#!/usr/bin/env python3
"""Regression checks for anchor validation and generated C++ (not a full Android NDK build)."""
from pathlib import Path
import tempfile
import subprocess
import sys
import re
import shutil

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import apply_source_patch as mod

MAIN = '''#include "Action.h"
class CMenuMain : public CMenuFramework {
\tCMenuAnimatedBanner animatedBanner;
\tCMenuMovieBanner movieBanner;
};
void CMenuMain::_Init() {
\tminimizeBtn.onReleased.SetCommand( false, "minimize\\n" );
\tAddItem( previews );
\tAddItem( quit );
\tAddItem( minimizeBtn );
\tAddItem( quitButton );
}
void CMenuMain::VidInit(bool connected) {
\tminimizeBtn.SetRect( uiStatic.width - 72, 13, 32, 32 );
\tquitButton.SetRect( uiStatic.width - 36, 13, 32, 32 );
}
'''

BROWSER = '''void CMenuServerBrowser::FavoriteServer() {
\tif( serv.favorite ) {
\t\tfavoritesList.AddToTail( entry );
\t}
\telse {
\t\tFOR_EACH_VEC( favoritesList, i ) {
\t\t\tfavoritesList.FastRemove(i);
\t\t}
\t}
}

void CMenuServerBrowser::MaybeEnableFavoriteButton( void )
{
}
void CMenuServerBrowser::AddServer( void ) {
\tfavlist_entry_t entry( addressField.GetBuffer(), proto, false );
\tfavoritesList.AddToTail( entry );
\tserver_t serv( adr, fakeInfoString, false, true );
\t\tgameListModel.AddServerToList( adr, fakeInfoString, false );
\tentry.QueryServer();
\tUI_MenuResetPing_f();
}
void CMenuServerBrowser::Show() {
\t\tfavoritesList.RemoveAll();
\t\thistoryList.RemoveAll();
\t\tif( EngFuncs::FileExists( "favorite_servers.lst", true ) )
\t\t\tParseServerListFromFile( "favorite_servers.lst", favoritesList );
\t\tif( EngFuncs::FileExists( "history_servers.lst", true ) )
\t\t\tParseServerListFromFile( "history_servers.lst", historyList );
}
'''

def check_cpp_command_literals(patched_main: str):
    """Compile precisely generated command definitions to catch malformed quote escaping."""
    commands = re.search(r'\tstatic const char \*const asiaCommands\[4\] = \{\n.*?\n\t\};', patched_main, re.S)
    assert commands, 'Missing commands in patched main menu'
    source = '#include <string>\nint main() {\n' + commands.group(0) + '\nreturn asiaCommands[0][0] != \'c\';\n}\n'
    with tempfile.TemporaryDirectory() as folder:
        sourcefile = Path(folder)/'commands.cpp'
        sourcefile.write_text(source)
        compiler = shutil.which('g++') or shutil.which('clang++')
        if compiler:
            run = subprocess.run([compiler, '-std=c++11', '-Wall', '-Wextra', '-Werror', '-fsyntax-only', str(sourcefile)], capture_output=True, text=True)
            assert run.returncode == 0, run.stderr
            return True
    return False

def main():
    assert len(mod.ADDRESSES) == len(set(mod.ADDRESSES)) == 18
    assert len(mod.LABELS) == 4
    assert len((BASE/'assets/cstrike/favorite_servers.lst').read_text().strip().splitlines()) == 18
    assert all(x.endswith(' gs') for x in (BASE/'assets/cstrike/favorite_servers.lst').read_text().strip().splitlines())
    with tempfile.TemporaryDirectory() as folder:
        repo = Path(folder)
        nested = repo/'3rdparty/mainui_cpp/menus'
        nested.mkdir(parents=True)
        mainfile, browserfile = nested/'Main.cpp', nested/'ServerBrowser.cpp'
        mainfile.write_text(MAIN)
        browserfile.write_text(BROWSER)
        script = BASE/'apply_source_patch.py'
        def go(*args):
            return subprocess.run([sys.executable, str(script), str(repo), *args], capture_output=True, text=True)
        check = go()
        assert check.returncode == 0, check.stderr
        assert mainfile.read_text() == MAIN
        assert browserfile.read_text() == BROWSER
        apply = go('--apply')
        assert apply.returncode == 0, apply.stderr
        main_cpp = mainfile.read_text()
        browser_cpp = browserfile.read_text()
        assert main_cpp.count('CMenuAction asiaPublic[4]') == 1
        assert main_cpp.count('AddItem( asiaPublic[i] )') == 1
        assert 'Top Player\'s ServeR' in main_cpp
        assert 'QM_TOPLEFT' in main_cpp and 'QM_LEFT;' not in main_cpp
        assert main_cpp.count('connect \\"Servercs.ir:') == 4
        assert check_cpp_command_literals(main_cpp)
        assert 'SetBackground' not in main_cpp
        assert browser_cpp.count('Servercs.ir:') == 18
        assert 'bool exists = false;' in browser_cpp
        assert 'stricmp( favoritesList[j].sadr, asiaServers[i] )' in browser_cpp
        assert 'asiagame_favorites_initialized.dat' in browser_cpp
        assert 'SaveServerListToFile( "favorite_servers.lst", favoritesList );' in browser_cpp
        # Three writes: toggle, AddServer, and initial seed.
        assert browser_cpp.count('SaveServerListToFile( "favorite_servers.lst", favoritesList );') == 3
        assert (mainfile.parent/'Main.cpp.asiagame.bak').read_text() == MAIN
        assert (browserfile.parent/'ServerBrowser.cpp.asiagame.bak').read_text() == BROWSER
        second = go('--apply')
        assert second.returncode != 0, 'Must not modify an already-patched source tree'
        # If one source anchor differs, dry run must not change either file.
        clean2 = repo/'other'; (clean2/'menus').mkdir(parents=True)
        (clean2/'menus/Main.cpp').write_text(MAIN)
        (clean2/'menus/ServerBrowser.cpp').write_text(BROWSER.replace('false, true', 'true, true'))
        failing = subprocess.run([sys.executable,str(script),str(clean2),'--apply'],capture_output=True,text=True)
        assert failing.returncode != 0
        assert (clean2/'menus/Main.cpp').read_text() == MAIN
        assert (clean2/'menus/ServerBrowser.cpp').read_text() != browser_cpp
    print('PASS: 18 seeds, 4 links, C++ command syntax, first-run merge, persistence, backups, reject incompatible source')

if __name__=='__main__': main()
