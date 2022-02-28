#ifndef __CLING__
#include <map>
#include <memory>
#include <set>
#include <string>
#include <string_view>
#include <vector>

#include <TFile.h>
#include <TH1.h>
#include <TKey.h>
#include <TObjArray.h>
#include <TObjString.h>
#include <TString.h>
#include <TSystem.h>
#endif

std::vector<TObject *> readFile(const std::string_view filename){
    std::vector<TObject *>result;
    std::unique_ptr<TFile> reader(TFile::Open(filename.data(), "READ"));
    for(auto entry : TRangeDynCast<TKey>(reader->GetListOfKeys())) {
        auto obj = entry->ReadObj();
        if(obj->InheritsFrom(TH1::Class())) {
            static_cast<TH1 *>(obj)->SetDirectory(nullptr);
        }
        result.push_back(obj);
    }
    return result;
}

std::set<std::string> getListOfFiles(const std::string_view inputdir){
    std::set<std::string> result;
    std::unique_ptr<TObjArray> content(gSystem->GetFromPipe(Form("ls -1 %s", inputdir.data())).Tokenize("\n"));
    for(auto en : TRangeDynCast<TObjString>(content.get())) {
        std::string currentdir = en->String().Data();
        std::string fpath = Form("%s/%s/Pythia8JetSpectra_merged.root", inputdir.data(), currentdir.data());;
        if(!gSystem->AccessPathName(fpath.data())){
            result.insert(currentdir);
        }
    }
    return result;
}

void CombineUncertaintyFile(const std::string_view inputdir = "."){
    std::map<std::string, std::vector<TObject *>> filecontets;
    std::string fullinputdir;
    if(inputdir == fullinputdir) {
        fullinputdir = gSystem->pwd();
    } else {
        fullinputdir = inputdir;
    }
    for(auto fl : getListOfFiles(fullinputdir)) {
        std::string filename = Form("%s/%s/Pythia8JetSpectra_merged.root", inputdir.data(), fl.data());
        filecontets[fl] = readFile(filename);
    }
    
    std::unique_ptr<TFile> writer(TFile::Open("POWHEGPYTHIA_sysvar.root", "RECREATE"));
    for(auto &[dirname, content] : filecontets) {
        writer->mkdir(dirname.data());
        writer->cd(dirname.data());
        for(auto obj : content) obj->Write(obj->GetName(), TObject::kSingleKey);
    }
}