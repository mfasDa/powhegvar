#ifndef __CLING__
#include <map>
#include <memory> 
#include <set>
#include <string>
#include <string_view>

#include <TCanvas.h>
#include <TFile.h>
#include <TH1.h>
#include <TKey.h>
#include <TLegend.h>
#include <TPaveText.h>
#include <ROOT/TSeq.hxx>
#endif

std::map<int, TH1 *> readFileScales(const char *filename){
    const std::vector<double> ptbinning = {0., 5., 10., 15., 20., 25., 30., 40., 50., 60., 70., 80., 90., 100., 110., 120., 130., 140., 160., 180., 200., 240., 280., 320.};
    std::map<int, TH1 *> result;
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
    for(auto R : ROOT::TSeqI(2, 7)) {
        auto centralRaw = reader->Get<TH1>(Form("jetspectrum_cent_R%02d", R));
        auto histCombined = centralRaw->Rebin(ptbinning.size()-1, "", ptbinning.data());
        histCombined->Scale(1., "width");
        histCombined->SetDirectory(nullptr);
        for(auto ib : ROOT::TSeqI(0, histCombined->GetNbinsX())) histCombined->SetBinError(ib+1, 0.);
        result[R] = histCombined;
    }
    return result;
}

std::map<int, TH1 *> readFilePDF(const char *filename){
    std::map<int, TH1 *> result;
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
    for(auto R : ROOT::TSeqI(2, 7)) {
        auto histCombined = reader->Get<TH1>(Form("SpectrumWithCombinedErrors_R%02d", R));
        histCombined->SetDirectory(nullptr);
        for(auto ib : ROOT::TSeqI(0, histCombined->GetNbinsX())) histCombined->SetBinError(ib+1, 0.);
        result[R] = histCombined;
    }
    return result;
}

void CompareCentralValues(const char *filescales = "POWHEGPYTHIA_jetspectrum_sys.root", const char *filepdf = "POWHEGPYTHIA_jetspectrum_syspdf.root") {
    auto dataScales = readFileScales(filescales),
         dataPDF = readFilePDF(filepdf);
    
    auto plot = new TCanvas("comparisonCentralValues", "Comparison central values", 1200, 800);
    plot->Divide(3,2);

    int ipad = 1;
    for(auto R : ROOT::TSeqI(2, 7)) {
        plot->cd(ipad);
        auto frame = new TH1F(Form("SpecFrame_R%02d", R), "; p_{t} (GeV/c); scale / pdf", 350, 0., 350.);
        frame->SetDirectory(nullptr);
        frame->SetStats(false);
        frame->GetYaxis()->SetRangeUser(0.8, 1.2);
        frame->Draw("axis");
        auto ratio = static_cast<TH1 *>(dataScales.find(R)->second->Clone(Form("RatioScalePDF_R%02d", R)));
        ratio->SetDirectory(nullptr);
        ratio->Divide(dataPDF.find(R)->second);
        ratio->SetMarkerStyle(20);
        ratio->SetMarkerColor(kBlack);
        ratio->SetLineColor(kBlack);
        ratio->Draw("epsame");
        ipad++;
    }
}