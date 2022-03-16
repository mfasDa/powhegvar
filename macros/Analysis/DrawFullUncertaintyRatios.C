#ifndef __CLING__
#include <map>
#include <memory> 
#include <set>
#include <string>
#include <string_view>

#include <TCanvas.h>
#include <TGraphAsymmErrors.h>
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
    TGraphAsymmErrors *mRelCombined;
    TGraphAsymmErrors *mRelScale;
    TGraphAsymmErrors *mRelPDF;


    bool operator==(const RBin &other) const { return mNumerator == other.mNumerator && mDenominator == other.mDenominator; }
    bool operator<(const RBin &other) const { if(mNumerator == other.mNumerator) return mDenominator < other.mDenominator; return mNumerator < other.mNumerator; }

    std::vector<double> getBinning(TGraphAsymmErrors * graph){
        std::set<double> binnningtmp;
        for(auto ip : ROOT::TSeqI(0, graph->GetN())) {
            double x = graph->GetX()[ip],
                   ex = graph->GetEXlow()[ip],
                   xmin = x - ex,
                   xmax = x + ex;
            if(binnningtmp.find(xmin) == binnningtmp.end()) binnningtmp.insert(xmin);
            if(binnningtmp.find(xmax) == binnningtmp.end()) binnningtmp.insert(xmax);
        }
        std::vector<double> binning;
        for(auto x : binnningtmp) binning.push_back(x);
        return binning;
    }

    std::pair<TH1 *, TH1 *> makeHistos(TGraphAsymmErrors * graph, const std::string_view source) {
        auto binning = getBinning(graph);
        TH1 *lower = new TH1D(Form("uncertaintyLow_%s_R%02dR%02d", source.data(), mNumerator, mDenominator), "", binning.size()-1, binning.data()),
            *upper = new TH1D(Form("uncertaintyHigh_%s_R%02dR%02d", source.data(), mNumerator, mDenominator), "", binning.size()-1, binning.data());
        lower->SetDirectory(nullptr);
        upper->SetDirectory(nullptr);
        for(int ip : ROOT::TSeqI(0, graph->GetN())) {
            double x = graph->GetX()[ip],
                   eylow = graph->GetEYlow()[ip],
                   eyhigh = graph->GetEYhigh()[ip];
            auto binID = lower->GetXaxis()->FindBin(x);
            lower->SetBinContent(binID, -1. * eylow);
            upper->SetBinContent(binID, eyhigh);
        }
        return {lower, upper};
    }

    void DrawErrors(TLegend *leg) {
        auto [combined_low, combined_high] = makeHistos(mRelCombined, "Combined");
        combined_low->SetLineColor(kBlack);
        combined_high->SetLineColor(kBlack);
        combined_low->Draw("boxsame");
        combined_high->Draw("boxsame");
        auto [scale_low, scale_high] = makeHistos(mRelScale, "Scale");
        scale_low->SetLineColor(kBlue);
        scale_high->SetLineColor(kBlue);
        scale_low->Draw("boxsame");
        scale_high->Draw("boxsame");
        auto [pdf_low, pdf_high] = makeHistos(mRelPDF, "PDF");
        pdf_low->SetLineColor(kRed);
        pdf_high->SetLineColor(kRed);
        pdf_low->Draw("boxsame");
        pdf_high->Draw("boxsame");
        if(leg) {
            leg->AddEntry(scale_low, "Scale", "l");
            leg->AddEntry(pdf_low, "PDF", "l");
            leg->AddEntry(combined_low, "Combined", "l");
        }
    }
};

TGraphAsymmErrors *makeRelError(TGraphAsymmErrors *spectrum) {
    auto result = new TGraphAsymmErrors;
    for(auto ib : ROOT::TSeqI(0, spectrum->GetN())) {
        double x = spectrum->GetX()[ib],
               y = spectrum->GetY()[ib],
               ex = spectrum->GetEXlow()[ib],
               eylow = spectrum->GetEYlow()[ib],
               eyhigh = spectrum->GetEYhigh()[ib];
        result->SetPoint(ib, x, 0.);
        result->SetPointError(ib, ex, ex, eylow/y, eyhigh/y);
    }
    return result;
}

std::vector<RBin> readFile(const char *filename) {
    std::vector<RBin> result;
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
    int numerator = 2;
    for(auto denominator : ROOT::TSeqI(3, 7)) {
        auto histCombined = makeRelError(reader->Get<TGraphAsymmErrors>(Form("jetspectrumratiofulljets_combineduncertainty_R%02dR%02d", numerator, denominator))),
             histScale = makeRelError(reader->Get<TGraphAsymmErrors>(Form("jetspectrumratiofulljets_scaleuncertainty_R%02dR%02d", numerator, denominator))),
             histPDF = makeRelError(reader->Get<TGraphAsymmErrors>(Form("jetspectrumratiofulljets_pdfuncertainty_R%02dR%02d", numerator, denominator)));
        RBin next;
        next.mNumerator = numerator;
        next.mDenominator = denominator;
        next.mRelCombined = histCombined;
        next.mRelPDF = histPDF;
        next.mRelScale = histScale;
        result.push_back(next);
    }
    std::sort(result.begin(), result.end(), std::less<RBin>());
    return result;
}

void DrawFullUncertaintyRatios(const char *filename = "POWHEGPYTHIA_13TeV_fulljets_ratios_withcorrelatedfullsys.root"){
    auto predictions = readFile(filename);
    auto plot = new TCanvas("POWHEGrelFullratios", "POWHEG rel. full uncertainty for 13 TeV pp ratios", 1000, 800);
    plot->Divide(2, 2);
    
    int ipad = 1;
    for(auto &rb : predictions) {
        plot->cd(ipad);
        gPad->SetLeftMargin(0.1);
        gPad->SetRightMargin(0.05);
        auto specframe = new TH1F(Form("specframeR%02dR%02d", rb.mNumerator, rb.mDenominator), "; p_{T} (GeV/c); rel. uncertainty", 350, 0., 350.);
        specframe->SetDirectory(nullptr);
        specframe->SetStats(false);
        specframe->GetYaxis()->SetRangeUser(-0.2, 0.2);
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