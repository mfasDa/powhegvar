#ifndef __CLING__
#include <memory>
#include "TFile.h"
#include "TKey.h"
#include "TObjArray.h"
#include "TString.h"
#include "TSystem.h"
#endif

void WriteDirectory(TDirectory *directory, const char *filebase, const char *dirname) {
    const char *indirname = directory->GetName();
    TString outfilename = Form("%s/%s_%s.root", dirname, filebase, indirname);    
    std::cout << "Writing outputfile " << outfilename << std::endl;
    std::unique_ptr<TFile> writer(TFile::Open(outfilename, "RECREATE"));
    writer->mkdir(indirname);
    writer->cd(indirname);
    for(auto obj : TRangeDynCast<TKey>(directory->GetListOfKeys())) {
        auto rootobj = obj->ReadObj();
        rootobj->Write(rootobj->GetName(), TObject::kSingleKey);
    }

}

void splitFile(const char *filename) {
    TString dirname = gSystem->DirName(filename);
    auto filebase = gSystem->BaseName(filename);
    TString filetag(filebase);
    filetag.ReplaceAll(".root", "");

    std::unique_ptr<TFile>reader(TFile::Open(filename, "READ"));
    TObjArray commoncontent;
    for(auto key : TRangeDynCast<TKey>(gDirectory->GetListOfKeys())) {
        auto rootobj = key->ReadObj();
        if(rootobj->InheritsFrom(TDirectory::Class())) {
            TDirectory *nextdir = static_cast<TDirectory *>(rootobj);
            WriteDirectory(nextdir, filetag.Data(), dirname.Data());
        } else {
            commoncontent.Add(rootobj);
        }
    }

    std::cout << "Writing common content " << std::endl;
    TString commonname = Form("%s/%s_common.root", dirname.Data(), filetag.Data());
    std::unique_ptr<TFile> writer(TFile::Open(commonname, "RECREATE"));
    for(auto rootobj : commoncontent) {
        rootobj->Write(rootobj->GetName(), TObject::kSingleKey);
    }
}