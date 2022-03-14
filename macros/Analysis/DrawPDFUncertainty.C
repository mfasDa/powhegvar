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

struct RBin {
    int mR;
    TH1 *mRelCombined;
    TH1 *mRelPDF;
    TH1 *mRelAlphas;

    bool operator==(const RBin &other) const { return mR == other.mR; }
    bool operator<(const RBin &other) const { return mR < other.mR; }

    void DrawErrors(TLegend *leg) {
        mRelCombined->SetLineColor(kBlack);
        mRelCombined->Draw("boxsame");
        mRelPDF->SetLineColor(kBlue);
        mRelPDF->Draw("boxsame");
        mRelAlphas->SetLineColor(kRed);
        mRelAlphas->Draw("boxsame");
        if(leg) {
            leg->AddEntry(mRelPDF, "PDF", "l");
            leg->AddEntry(mRelAlphas, "#alpha_{s}", "l");
            leg->AddEntry(mRelCombined, "Combined", "l");
        }
    }
};

TH1 *makeRelError(TH1 *spectrum, int R) {
    auto result = static_cast<TH1 *>(spectrum->Clone(Form("relError_combined_%02d", R)));
    result->SetDirectory(nullptr);
    result->Reset();
    for(auto ib : ROOT::TSeqI(0, spectrum->GetXaxis()->GetNbins())) {
        double value = spectrum->GetBinContent(ib+1),
               error = spectrum->GetBinError(ib+1);
        result->SetBinContent(ib+1, error/value);
        result->SetBinError(ib+1, 0);
    }
    return result;
}

std::vector<RBin> readFile(const char *filename) {
    std::vector<RBin> result;
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
    for(auto R : ROOT::TSeqI(2, 7)) {
        auto histCombined = makeRelError(reader->Get<TH1>(Form("SpectrumWithCombinedErrors_R%02d", R)), R),
             histPDF = reader->Get<TH1>(Form("relError_pdf_%02d", R)),
             histAlphas = reader->Get<TH1>(Form("relError_alphas_%02d", R));
        histPDF->SetDirectory(nullptr);
        histAlphas->SetDirectory(nullptr);
        RBin next;
        next.mR = R;
        next.mRelCombined = histCombined;
        next.mRelPDF = histPDF;
        next.mRelAlphas = histAlphas;
        result.push_back(next);
    }
    std::sort(result.begin(), result.end(), std::less<RBin>());
    return result;
}

void DrawPDFUncertainty(const char *filename = "POWHEGPYTHIA_jetspectrum_syspdf.root"){
    auto predictions = readFile(filename);
    auto plot = new TCanvas("POWHEGrelPDF", "POWHEG rel. PDF uncertainty for 13 TeV pp", 1200, 800);
    plot->Divide(3, 2);
    
    int ipad = 1;
    for(auto &rb : predictions) {
        plot->cd(ipad);
        gPad->SetLeftMargin(0.15);
        gPad->SetRightMargin(0.05);
        auto specframe = new TH1F(Form("specframeR%02d", rb.mR), "; p_{T} (GeV/c); rel. uncertainty", 350, 0., 350.);
        specframe->SetDirectory(nullptr);
        specframe->SetStats(false);
        specframe->GetYaxis()->SetRangeUser(0., 0.2);
        specframe->Draw("axis");
        auto label = new TPaveText(0.15, 0.8, 0.35, 0.89, "NDC");
        label->SetBorderSize(0);
        label->SetFillStyle(0);
        label->SetTextSize(0.045);
        label->SetTextFont(42);
        label->AddText(Form("R = %.1f", double(rb.mR) / 10.));
        label->Draw();
        TLegend *leg = nullptr;
        if(ipad == 1) {
            leg = new TLegend(0.5, 0.7, 0.89, 0.89);
            leg->SetBorderSize(0);
            leg->SetFillStyle(0);
            leg->SetTextFont(42);
            leg->Draw();
        }
        rb.DrawErrors(leg);
        ipad++;
    }
    plot->cd();
    plot->Update();
    plot->SaveAs(Form("%s.png", plot->GetName()));
}