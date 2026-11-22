#!/usr/bin/env python3
"""Native C++ mock-ABI smoke tests: compiles generated code, runs seeding behavior.
This deliberately does NOT assert compatibility with the real Android engine ABI.
"""
from pathlib import Path
import sys
import subprocess
import tempfile
import re

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
import apply_source_patch as patch

# Same unique upstream anchors as actual files, reduced to lines that v4 changes.
from test_patch import MAIN, BROWSER
m=patch.patch_main(MAIN)
b=patch.patch_server_browser(BROWSER)

# Mock out exactly public members our injection uses; compile the actual transformed
# menu function, not rewritten Python copies of the behavior.
main_stub=r'''
struct Ui { int width=1024; } uiStatic; // Matches real uiStatic_t: NO height member.
struct Callback { void SetCommand(bool, const char*) {} };
struct MenuItem {
    Callback onReleased;
    unsigned int iFlags=0;
    unsigned int colorBase=0,colorFocus=0,eTextAlignment=0;
    int eFocusAnimation=0;
    void SetNameAndStatus(const char*,const char*) {}
    void SetCharSize(int) {}
    void SetRect(int,int,int,int) {}
};
struct CMenuAnimatedBanner : MenuItem {};
struct CMenuMovieBanner : MenuItem {};
struct CMenuFramework { void AddItem(MenuItem&) {} };
static const int QM_SMALLFONT=1,QM_HIGHLIGHTIFFOCUS=2,QM_TOPLEFT=3;
static const unsigned int QMF_NOTIFY=4;
class CMenuMain : public CMenuFramework {
public:
    CMenuAnimatedBanner animatedBanner;
    CMenuMovieBanner movieBanner;
    MenuItem console,resumeGame,disconnect,newGame,hazardCourse,configuration;
    MenuItem saveRestore,multiPlayer,customGame,previews,quit;
    MenuItem minimizeBtn,quitButton;
    // This class declaration will be expanded with four ASiA-GaME items.
    void _Init();
    void VidInit(bool);
};
'''
main_stub=main_stub.replace('    // This class declaration will be expanded with four ASiA-GaME items.','    MenuItem asiaPublic[4];')
main_funcs=m[m.index('void CMenuMain::_Init()'):]
main_func_stub=main_stub+'\n'+main_funcs+'\nint main() { CMenuMain menu;menu._Init();menu.VidInit(false);}\n'

# Lift real generated first-run code, simulate filesystem persistence with in-memory
# vectors, and execute on first/second launch. Mocked filesystem checks are not an
# Android filesystem test.
start=b.index('\t\tfavoritesList.RemoveAll();')
stop=b.index('\t\t\tParseServerListFromFile( "history_servers.lst", historyList );',start)
seed=b[start:stop+len('\t\t\tParseServerListFromFile( "history_servers.lst", historyList );')]
browser_stub=r'''
#include <vector>
#include <string>
#include <map>
#include <cstdio>
#include <cstring>
#include <strings.h>
#include <cassert>
#include <utility>
struct Item { std::string sadr,prot; bool favorited; Item(const char*a,const char*b,bool f=true):sadr(a),prot(b),favorited(f){} };
struct Vector {
 std::vector<Item> a;
 void RemoveAll(){ a.clear(); }
 void AddToTail(const Item&x){a.push_back(x);}
 unsigned Count() const{return a.size();}
 Item& operator[](unsigned i){return a[i];}
};
#define FOR_EACH_VEC(x,j) for(unsigned j=0;j<(x).Count();j++)
int stricmp(const char*a,const char*b){return strcasecmp(a,b);}
int stricmp(const std::string&a,const char*b){return strcasecmp(a.c_str(),b);}
using favlist_entry_t=Item;
static std::map<std::string,std::vector<Item>> data;
static std::map<std::string,std::string> markers;
struct EngFuncs {
 static bool FileExists(const char*f,bool){return data.count(f)>0||markers.count(f)>0;}
 static void COM_SaveFile(const char*f,const char*v,int n){markers[f]=std::string(v,n);}
};
struct Browser {
 Vector favoritesList,historyList;
 void ParseServerListFromFile(const char* f,Vector &v){ for(auto &x:data[f])v.AddToTail(x); }
 void SaveServerListToFile(const char* f,const Vector&v){if(v.a.empty())data.erase(f);else data[f]=v.a;}
 void Show(){
'''+seed+r'''
 }
};
int main(){
 data["favorite_servers.lst"]={Item("old-host:23000","gs"), Item("Servercs.ir:27015","gs")};
 Browser browser; browser.Show();
 assert(browser.favoritesList.Count()==19);
 assert(markers["asiagame_favorites_initialized.dat"]=="1\n");
 assert(data["favorite_servers.lst"].size()==19);
 // A deliberate user deletion must not restore defaults on the next launch.
 data.erase("favorite_servers.lst");
 Browser afterDeletion; afterDeletion.Show();
 assert(afterDeletion.favoritesList.Count()==0);
 // Fresh installation without any state gets exactly 18 defaults.
 markers.clear();data.clear();
 Browser fresh;fresh.Show();
 assert(fresh.favoritesList.Count()==18);
 assert(data["favorite_servers.lst"].size()==18);
 puts("PASS: native C++ first-launch merge and persistent deletion logic");
}
'''

def compile_run(source,name):
    with tempfile.TemporaryDirectory() as t:
        src=Path(t)/(name+'.cpp');exe=Path(t)/(name)
        src.write_text(source)
        cmd=['g++','-std=c++11','-Wall','-Wextra','-Werror','-Wno-unused-variable','-Wno-unused-parameter',str(src),'-o',str(exe)]
        res=subprocess.run(cmd,capture_output=True,text=True)
        if res.returncode: print(src.read_text(),file=sys.stderr);raise AssertionError(f'{name} compile: '+res.stderr)
        run=subprocess.run([str(exe)],capture_output=True,text=True)
        assert run.returncode==0,run.stderr
        print(name,run.stdout.strip())
compile_run(main_func_stub,'menu_cpp')
compile_run(browser_stub,'favorites_cpp')
