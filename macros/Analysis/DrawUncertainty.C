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
#include <TPaveText.h>
#include <ROOT/TSeq.hxx>
#endif

struct Rbin{
    int mR;
    TH1 *mCentral;
    TH1 *mLower;
    TH1 *mUpper;

    bool operator==(const Rbin &other) const { return mR == other.mR; }
    bool operator<(const Rbin &other) const { return mR == other.mR; }

    void DrawSpectrum() {
        mCentral->SetLineColor(kRed);
        mCentral->Draw("boxsame");
        mLower->SetLineColor(kBlue);
        mLower->Draw("boxsame");
        mUpper->SetLineColor(kBlue);
        mUpper->Draw("boxsame");
    }

    void DrawRatio() {
        auto ratiolow = static_cast<TH1 *>(mLower->Clone(Form("RatioLow_R%02d", mR)));
        ratiolow->SetDirectory(nullptr);
        ratiolow->SetLineColor(kBlue);
        ratiolow->Divide(mCentral);
        ratiolow->Draw("boxsame");
        auto ratiohigh = static_cast<TH1 *>(mUpper->Clone(Form("RatioHigh_R%02d", mR)));
        ratiohigh->SetDirectory(nullptr);
        ratiohigh->SetLineColor(kBlue);
        ratiohigh->Divide(mCentral);
        ratiohigh->Draw("boxsame");
        auto cent = static_cast<TH1 *>(mCentral->Clone(Form("RatioCent_R%02d", mR)));
        cent->SetDirectory(nullptr);
        cent->SetLineColor(kRed);
        for(auto ib : ROOT::TSeqI(0,cent->GetXaxis()->GetNbins())) {
            cent->SetBinContent(ib+1, 1);
            cent->SetBinError(ib+1, 0);
        }
        cent->Draw("boxsame");
    }
};

std::vector<Rbin> readFile(const std::string_view filename) {
    std::vector<Rbin> result;
    std::unique_ptr<TFile> reader(TFile::Open(filename.data(), "READ"));
    for(auto R : ROOT::TSeqI(2, 7)) {
        Rbin nextbin;
        nextbin.mR = R;
        nextbin.mCentral = reader->Get<TH1>(Form("jetspectrum_cent_R%02d", R));
        nextbin.mLower = reader->Get<TH1>(Form("jetspectrum_low_R%02d", R));
        nextbin.mUpper = reader->Get<TH1>(Form("jetspectrum_high_R%02d", R));
        nextbin.mCentral->SetDirectory(nullptr);
        nextbin.mLower->SetDirectory(nullptr);
        nextbin.mUpper->SetDirectory(nullptr);
        result.push_back(nextbin);
    }
    std::sort(result.begin(), result.end(), std::less<Rbin>());
    return result;
}


void DrawUncertainty(const std::string_view filename = "POWHEGPYTHIA_jetspectrum_sys.root"){
    auto predictions = readFile(filename);
    
    auto plot = new TCanvas("powhegfine13TeV", "POWHEG predicitions for 13 TeV pp", 1200, 600);
    plot->Divide(5, 2);
    
    int icol = 0;
    for(auto &rb : predictions) {
        plot->cd(icol+1);
        gPad->SetLogy();
        gPad->SetLeftMargin(0.15);
        gPad->SetRightMargin(0.05);
        auto specframe = new TH1F(Form("specframeR%02d", rb.mR), "; p_{T} (GeV/c); d#sigma/dp_{t}dy (mb/(GeV/c))", 350, 0., 350.);
        specframe->SetDirectory(nullptr);
        specframe->SetStats(false);
        specframe->GetYaxis()->SetRangeUser(1e-10, 1000);
        specframe->Draw("axis");
        auto label = new TPaveText(0.65, 0.8, 0.89, 0.89, "NDC");
        label->SetBorderSize(0);
        label->SetFillStyle(0);
        label->SetTextSize(0.045);
        label->SetTextFont(42);
        label->AddText(Form("R = %.1f", double(rb.mR) / 10.));
        label->Draw();
        rb.DrawSpectrum();

        plot->cd(icol+5+1);
        gPad->SetLeftMargin(0.15);
        gPad->SetRightMargin(0.05);
        auto ratioframe = new TH1F(Form("ratioframeR%02d", rb.mR), "; p_{T} (GeV/c); rel. uncertainty", 350, 0., 350.);
        ratioframe->SetDirectory(nullptr);
        ratioframe->SetStats(false);
        ratioframe->GetYaxis()->SetRangeUser(0., 2.);
        ratioframe->Draw("axis");
        rb.DrawRatio();
        icol++;
    }
    plot->cd();
    plot->Update();
    plot->SaveAs(Form("%s.png", plot->GetName()));
}