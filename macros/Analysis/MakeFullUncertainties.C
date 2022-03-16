#ifndef __CLING__
#include <iostream>
#include <cmath>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <string_view>
#include <vector>

#include <TFile.h>
#include <TGraphAsymmErrors.h>
#include <TH1.h>
#include <TKey.h>

#include <ROOT/TSeq.hxx>
#endif

struct FullSystematics {
    TGraphAsymmErrors *mCombined;
    TGraphAsymmErrors *mScale;
    TGraphAsymmErrors *mPDF;
};

std::map<int, TGraphAsymmErrors *> readScaleUncertainty(const char *filename){
    std::map<int, TGraphAsymmErrors *> result;
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
    for(auto R : ROOT::TSeqI(2, 7)) {
        auto histCombined = reader->Get<TGraphAsymmErrors>(Form("jetspectrumfulljets_R%02d", R));
        histCombined->SetName(Form("jetspectrumfulljets_scale_R%02d", R));
        result[R] = histCombined;
    }
    return result;
}

std::map<int, TH1 *> readPDFUncertainty(const char *filename){
    std::map<int, TH1 *> result;
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
    for(auto R : ROOT::TSeqI(2, 7)) {
        auto histCombined = reader->Get<TH1>(Form("SpectrumWithCombinedErrors_R%02d", R));
        histCombined->SetDirectory(nullptr);
        result[R] = histCombined;
    }
    return result;
}

TGraphAsymmErrors *makeGraphPDFUncertainty(TH1 *dataPDF, int R) {
    TGraphAsymmErrors *result = new TGraphAsymmErrors;
    result->SetName(Form("jetspectrumfulljets_pdf_R%02d", R));
    int npoint = 0;
    for(auto ib : ROOT::TSeqI(0, dataPDF->GetXaxis()->GetNbins())) {
        double x = dataPDF->GetXaxis()->GetBinCenter(ib+1),
               ex = dataPDF->GetXaxis()->GetBinWidth(ib+1)/2.,
               y = dataPDF->GetBinContent(ib+1),
               ey = dataPDF->GetBinError(ib+1);
        result->SetPoint(npoint, x, y);
        result->SetPointError(npoint, ex, ex, ey, ey);
        npoint++;
    }
    return result;
}

TGraphAsymmErrors * makeCombinedUncertainty(TGraphAsymmErrors *dataScale, TH1 *dataPDF, int R) {
    TGraphAsymmErrors *result = new TGraphAsymmErrors;
    result->SetName(Form("jetspectrumfulljets_R%02d", R));
    for(auto ipt : ROOT::TSeqI(0, dataScale->GetN())) {
        double x = dataScale->GetX()[ipt],
               y = dataScale->GetY()[ipt],
               ex = dataScale->GetEXhigh()[ipt],
               eyl_scale = dataScale->GetEYlow()[ipt],
               eyh_scale = dataScale->GetEYhigh()[ipt];
        int binPDF = dataPDF->GetXaxis()->FindBin(x);
        double ey_pdf = dataPDF->GetBinError(binPDF);
        double eyl_full = std::sqrt(eyl_scale*eyl_scale + ey_pdf*ey_pdf),
               eyh_full = std::sqrt(eyh_scale*eyh_scale + ey_pdf*ey_pdf);
        result->SetPoint(ipt, x, y);
        result->SetPointError(ipt, ex, ex, eyl_full, eyh_full);
    }
    return result;
}

FullSystematics build(TGraphAsymmErrors *dataScale, TH1 *dataPDF, int R) {
    auto *graphPDF = makeGraphPDFUncertainty(dataPDF, R),
         *graphCombined = makeCombinedUncertainty(dataScale, dataPDF, R);
    return {graphCombined, dataScale, graphPDF};
}

void MakeFullUncertainties(const char *filescale = "POWHEGPYTHIA_13TeV_fulljets_withscalesys.root", const char *filepdf = "POWHEGPYTHIA_jetspectrum_syspdf.root"){
    auto dataScale = readScaleUncertainty(filescale);
    auto dataPDF = readPDFUncertainty(filepdf);

    std::unique_ptr<TFile> writer(TFile::Open("POWHEGPYTHIA_13TeV_fulljets_withfullsys.root ", "RECREATE"));
    for(auto R : ROOT::TSeqI(2, 7)){
        auto combined = build(dataScale.find(R)->second, dataPDF.find(R)->second, R);
        combined.mCombined->Write();
        combined.mScale->Write();
        combined.mPDF->Write();
    }
}