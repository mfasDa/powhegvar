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
    int mNumerator;
    int mDenominator;
    TH1 *mRelCombined;
    TH1 *mRelPDF;
    TH1 *mRelAlphas;

    bool operator==(const RBin &other) const { return mNumerator == other.mNumerator && mDenominator == other.mDenominator; }
    bool operator<(const RBin &other) const { if(mNumerator == other.mNumerator) return mDenominator < other.mDenominator; return mNumerator < other.mNumerator; }

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

TH1 *makeRelError(TH1 *spectrum, int numerator, int denominator) {
    auto result = static_cast<TH1 *>(spectrum->Clone(Form("relError_combined_R%02dR%02d", numerator, denominator)));
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
    int numerator = 2;
    for(auto denominator : ROOT::TSeqI(3, 7)) {
        auto histCombined = makeRelError(reader->Get<TH1>(Form("SpectrumRatioWithCombinedErrors_R%02dR%02d", numerator, denominator)), numerator, denominator),
             histPDF = reader->Get<TH1>(Form("relError_pdf_R%02dR%d", numerator, denominator)),
             histAlphas = reader->Get<TH1>(Form("relError_alphas_R%02dR%d", numerator, denominator));
        histPDF->SetDirectory(nullptr);
        histAlphas->SetDirectory(nullptr);
        RBin next;
        next.mNumerator = numerator;
        next.mDenominator = denominator;
        next.mRelCombined = histCombined;
        next.mRelPDF = histPDF;
        next.mRelAlphas = histAlphas;
        result.push_back(next);
    }
    std::sort(result.begin(), result.end(), std::less<RBin>());
    return result;
}

void DrawPDFUncertaintyRatios(const char *filename = "POWHEGPYTHIA_jetspectrumratio_syspdf.root"){
    auto predictions = readFile(filename);
    auto plot = new TCanvas("POWHEGrelPDFratios", "POWHEG rel. PDF uncertainty for 13 TeV pp ratios", 1000, 800);
    plot->Divide(2, 2);
    
    int ipad = 1;
    for(auto &rb : predictions) {
        plot->cd(ipad);
        gPad->SetLeftMargin(0.1);
        gPad->SetRightMargin(0.05);
        auto specframe = new TH1F(Form("specframeR%02dR%02d", rb.mNumerator, rb.mDenominator), "; p_{T} (GeV/c); rel. uncertainty", 350, 0., 350.);
        specframe->SetDirectory(nullptr);
        specframe->SetStats(false);
        specframe->GetYaxis()->SetRangeUser(0., 0.1);
        specframe->Draw("axis");
        auto label = new TPaveText(0.15, 0.8, 0.45, 0.89, "NDC");
        label->SetBorderSize(0);
        label->SetFillStyle(0);
        label->SetTextSize(0.045);
        label->SetTextFont(42);
        label->AddText(Form("R = %.1f / R = %.1f", double(rb.mNumerator) / 10., double(rb.mDenominator) / 10.));
        label->Draw();
        TLegend *leg = nullptr;
        if(ipad == 1) {
            leg = new TLegend(0.7, 0.7, 0.95, 0.89);
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
    std::vector<std::string> formats = {"eps", "pdf", "png"};
    for(auto &form : formats) plot->SaveAs(Form("%s.%s", plot->GetName(), form.data()));
}