#!/usr/bin/env python3
"""ASiA-GaME source customizations for the cs16-client mainui_cpp submodule.

This edits *source files* (menus/Main.cpp, menus/ServerBrowser.cpp), never an APK.
Default mode validates patch anchors without modifying anything.
Usage: python3 apply_source_patch.py /path/to/cs16-client [--apply]
"""
from __future__ import annotations
import argparse
from pathlib import Path
import difflib
import shutil
import sys

ADDRESSES = (
    "Servercs.ir:27015", "Servercs.ir:27013", "Servercs.ir:27022", "Servercs.ir:27012",
    "Servercs.ir:27011", "Servercs.ir:27018", "Servercs.ir:27090", "Servercs.ir:27025",
    "Servercs.ir:27020", "Servercs.ir:27024", "Servercs.ir:27016", "Servercs.ir:27026",
    "Servercs.ir:27019", "Servercs.ir:27021", "Servercs.ir:27023", "Servercs.ir:27000",
    "Servercs.ir:27017", "Servercs.ir:27014",
)
assert len(ADDRESSES) == 18 and len(set(ADDRESSES)) == 18

LABELS = (
    "ASiA-GaME | Top Player's ServeR",
    "ASiA-GaME | Public 2",
    "ASiA-GaME | Public 3",
    "ASiA-GaME | Public 4",
)

class PatchError(Exception):
    pass

def replace_once(src: str, before: str, after: str, name: str) -> str:
    if src.count(before) == 1:
        return src.replace(before, after, 1)
    if after in src and before not in src:
        raise PatchError(f'{name}: source seems already patched; use a clean upstream source copy.')
    raise PatchError(f'{name}: expected anchor count = 1, got {src.count(before)}; upstream revision differs.')

def patch_main(src: str) -> str:
    src = replace_once(src,
        '\tCMenuAnimatedBanner animatedBanner;\n\tCMenuMovieBanner movieBanner;\n',
        '\tCMenuAnimatedBanner animatedBanner;\n\tCMenuMovieBanner movieBanner;\n\tCMenuAction asiaPublic[4]; // text-only clickable links\n',
        'Main: new actions')

    anchor = '\tminimizeBtn.onReleased.SetCommand( false, "minimize\\n" );\n'
    addition = '''\n\t// ASiA-GaME: only text, with no background rectangle or texture.
\tstatic const char *const asiaLabels[4] = {
\t\t"ASiA-GaME | Top Player's ServeR",
\t\t"ASiA-GaME | Public 2",
\t\t"ASiA-GaME | Public 3",
\t\t"ASiA-GaME | Public 4"
\t};
\tstatic const char *const asiaCommands[4] = {
\t\t"connect \\\"Servercs.ir:27015\\\" \\\"gs\\\"\\n",
\t\t"connect \\\"Servercs.ir:27013\\\" \\\"gs\\\"\\n",
\t\t"connect \\\"Servercs.ir:27022\\\" \\\"gs\\\"\\n",
\t\t"connect \\\"Servercs.ir:27012\\\" \\\"gs\\\"\\n"
\t};
\tfor( int i = 0; i < 4; ++i )
\t{
\t\tasiaPublic[i].SetNameAndStatus( asiaLabels[i], nullptr );
\t\tasiaPublic[i].SetCharSize( QM_SMALLFONT );
\t\tasiaPublic[i].colorBase = 0xFFFFAB4A; // orange lettering, full alpha
\t\tasiaPublic[i].colorFocus = 0xFFFFFFFF; // white on tap/selection
\t\tasiaPublic[i].eFocusAnimation = QM_HIGHLIGHTIFFOCUS;
\t\tasiaPublic[i].eTextAlignment = QM_TOPLEFT;
\t\tasiaPublic[i].onReleased.SetCommand( false, asiaCommands[i] );
\t}
\n\t// Hide help descriptions only; retain original main-menu items.
\tconsole.iFlags &= ~QMF_NOTIFY;
\tresumeGame.iFlags &= ~QMF_NOTIFY;
\tdisconnect.iFlags &= ~QMF_NOTIFY;
\tnewGame.iFlags &= ~QMF_NOTIFY;
\thazardCourse.iFlags &= ~QMF_NOTIFY;
\tconfiguration.iFlags &= ~QMF_NOTIFY;
\tsaveRestore.iFlags &= ~QMF_NOTIFY;
\tmultiPlayer.iFlags &= ~QMF_NOTIFY;
\tcustomGame.iFlags &= ~QMF_NOTIFY;
\tpreviews.iFlags &= ~QMF_NOTIFY;
\tquit.iFlags &= ~QMF_NOTIFY;
'''
    src = replace_once(src, anchor, anchor + addition, 'Main: link actions and suppress tooltips')
    src = replace_once(src,
        '\tAddItem( previews );\n\tAddItem( quit );\n\tAddItem( minimizeBtn );\n',
        '\tAddItem( previews );\n\tAddItem( quit );\n\tfor( int i = 0; i < 4; ++i )\n\t\tAddItem( asiaPublic[i] );\n\tAddItem( minimizeBtn );\n',
        'Main: register clickable text')
    src = replace_once(src,
        '\tminimizeBtn.SetRect( uiStatic.width - 72, 13, 32, 32 );\n\tquitButton.SetRect( uiStatic.width - 36, 13, 32, 32 );\n',
        '''\tminimizeBtn.SetRect( uiStatic.width - 72, 13, 32, 32 );
\tquitButton.SetRect( uiStatic.width - 36, 13, 32, 32 );
\t// mainui_cpp uses 768 logical vertical units; uiStatic_t has width but no height.
\tconst int asiaX = uiStatic.width * 56 / 100;
\tconst int asiaY = 768 * 35 / 100;
\tconst int asiaRow = 768 * 7 / 100;
\tfor( int i = 0; i < 4; ++i )
\t\tasiaPublic[i].SetRect( asiaX, asiaY + i * asiaRow,
\t\t\tuiStatic.width - asiaX - 16, asiaRow );
''', 'Main: responsive link positions')
    return src


def patch_server_browser(src: str) -> str:
    # Favoriting/unfavoriting is a user action: both directions must persist.
    src = replace_once(src,
        '\t}\n}\n\nvoid CMenuServerBrowser::MaybeEnableFavoriteButton( void )\n',
        '\t}\n\t// ASiA-GaME: persist Favorite / Unfavorite without depending on closing the menu.\n\tSaveServerListToFile( "favorite_servers.lst", favoritesList );\n}\n\nvoid CMenuServerBrowser::MaybeEnableFavoriteButton( void )\n',
        'Browser: persist FavoriteServer toggles')

    src = replace_once(src,
        '\tfavlist_entry_t entry( addressField.GetBuffer(), proto, false );\n',
        '\tfavlist_entry_t entry( addressField.GetBuffer(), proto, true );\n',
        'Browser: AddServer favorite flag')
    src = replace_once(src,
        '\tserver_t serv( adr, fakeInfoString, false, true );\n',
        '\tserver_t serv( adr, fakeInfoString, true, true );\n',
        'Browser: AddServer row favorite')
    src = replace_once(src,
        '\t\tgameListModel.AddServerToList( adr, fakeInfoString, false );\n',
        '\t\tgameListModel.AddServerToList( adr, fakeInfoString, true );\n',
        'Browser: AddServer model favorite')
    src = replace_once(src,
        '\tentry.QueryServer();\n\tUI_MenuResetPing_f();\n',
        '\tentry.QueryServer();\n\tSaveServerListToFile( "favorite_servers.lst", favoritesList );\n\tUI_MenuResetPing_f();\n',
        'Browser: persist newly added server')

    before = '''\t\tfavoritesList.RemoveAll();
\t\thistoryList.RemoveAll();
\t\tif( EngFuncs::FileExists( "favorite_servers.lst", true ) )
\t\t\tParseServerListFromFile( "favorite_servers.lst", favoritesList );
\t\tif( EngFuncs::FileExists( "history_servers.lst", true ) )
\t\t\tParseServerListFromFile( "history_servers.lst", historyList );
'''
    server_rows = '\n'.join(f'\t\t\t\t"{address}",' for address in ADDRESSES).rstrip(',')
    after = '''\t\tfavoritesList.RemoveAll();
\t\thistoryList.RemoveAll();
\t\t// ASiA-GaME: preserve old Favorites and append missing defaults ONCE.
\t\tif( EngFuncs::FileExists( "favorite_servers.lst", true ) )
\t\t\tParseServerListFromFile( "favorite_servers.lst", favoritesList );
\t\tif( !EngFuncs::FileExists( "asiagame_favorites_initialized.dat", true ) )
\t\t{
\t\t\tstatic const char *const asiaServers[] = {
''' + server_rows + '''
\t\t\t};
\t\t\tfor( unsigned int i = 0; i < sizeof( asiaServers ) / sizeof( asiaServers[0] ); ++i )
\t\t\t{
\t\t\t\tbool exists = false;
\t\t\t\tFOR_EACH_VEC( favoritesList, j )
\t\t\t\t{
\t\t\t\t\tif( !stricmp( favoritesList[j].sadr, asiaServers[i] ) &&
\t\t\t\t\t    !stricmp( favoritesList[j].prot, "gs" ) )
\t\t\t\t\t{
\t\t\t\t\t\texists = true;
\t\t\t\t\t\tbreak;
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tif( !exists )
\t\t\t\t\tfavoritesList.AddToTail( favlist_entry_t( asiaServers[i], "gs", true ) );
\t\t\t}
\t\t\tSaveServerListToFile( "favorite_servers.lst", favoritesList );
\t\t\tstatic const char initMarker[] = "1\\n";
\t\t\tEngFuncs::COM_SaveFile( "asiagame_favorites_initialized.dat", initMarker, sizeof( initMarker ) - 1 );
\t\t}
\t\tif( EngFuncs::FileExists( "history_servers.lst", true ) )
\t\t\tParseServerListFromFile( "history_servers.lst", historyList );
'''
    src = replace_once(src, before, after, 'Browser: merge favorites and first-run seed')
    return src


def run(source_dir: Path, apply: bool) -> int:
    if (source_dir / '3rdparty' / 'mainui_cpp' / 'menus' / 'Main.cpp').is_file():
        source_dir = source_dir / '3rdparty' / 'mainui_cpp'
        print(f'SUBMODULE: {source_dir}')
    elif not (source_dir / 'menus' / 'Main.cpp').is_file():
        raise PatchError('Expected cs16-client tree with --recursive submodule at 3rdparty/mainui_cpp')
    files = {
        'menus/Main.cpp': patch_main,
        'menus/ServerBrowser.cpp': patch_server_browser,
    }
    pending = {}
    for rel, patch in files.items():
        path = source_dir / rel
        if not path.is_file():
            raise PatchError(f'Missing source file: {path}')
        original = path.read_bytes()
        if b'\r\n' in original:
            raise PatchError(f'{rel}: CRLF line endings unsupported. Convert to LF before patching.')
        updated = patch(original.decode('utf-8'))
        pending[path] = (original, updated.encode('utf-8'))
        print(f'VALIDATED: {rel} ({len(original)} -> {len(updated.encode("utf-8"))} bytes)')

    if not apply:
        print('CHECK ONLY: no files changed. Run with --apply to write .asiagame.bak backups and update source.')
        return 0

    for path in pending:
        backup = path.with_name(path.name + '.asiagame.bak')
        if backup.exists():
            raise PatchError(f'Backup already exists, refusing overwrite: {backup}')
    for path, (old, updated) in pending.items():
        backup = path.with_name(path.name + '.asiagame.bak')
        backup.write_bytes(old)
        path.write_bytes(updated)
        print(f'PATCHED: {path} (backup: {backup})')
    print('Done: SOURCE changes only. Native libraries still require NDK build and APK signing.')
    return 0

if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('source_dir', type=Path, help='Root of cs16-client checkout (or direct mainui_cpp submodule)')
    cli.add_argument('--apply', action='store_true', help='Apply source edits after validation and back up originals')
    args = cli.parse_args()
    try:
        sys.exit(run(args.source_dir.resolve(), args.apply))
    except (PatchError, UnicodeDecodeError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
