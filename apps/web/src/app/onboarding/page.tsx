"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { createClient } from "@/lib/supabase";
import { useAuth } from "@/lib/auth-context";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { TrendingUp, ChevronRight, ChevronLeft } from "lucide-react";

interface Question {
  id: string;
  text: string;
  dimension: "volatility" | "horizon" | "knowledge" | "general";
  options: { label: string; score: number }[];
}

const questions: Question[] = [
  {
    id: "experience",
    text: "What is your investment experience?",
    dimension: "knowledge",
    options: [
      { label: "New to investing (less than 1 year)", score: 1 },
      { label: "Some experience (1-3 years)", score: 2 },
      { label: "Intermediate (3-7 years)", score: 3 },
      { label: "Experienced investor (7+ years)", score: 4 },
    ],
  },
  {
    id: "market_knowledge",
    text: "How well do you understand financial markets and instruments?",
    dimension: "knowledge",
    options: [
      { label: "Basic — I know about savings accounts and FDs", score: 1 },
      { label: "Fair — I understand mutual funds and index investing", score: 2 },
      { label: "Good — I understand stocks, sectors, and P/E ratios", score: 3 },
      { label: "Advanced — I can read charts, options, and financial statements", score: 4 },
    ],
  },
  {
    id: "risk_tolerance",
    text: "How would you describe your risk tolerance?",
    dimension: "volatility",
    options: [
      { label: "I prefer safety over returns — capital preservation is key", score: 1 },
      { label: "I can accept small dips for moderate growth", score: 2 },
      { label: "I can tolerate significant swings for higher returns", score: 3 },
      { label: "I actively seek high-risk, high-reward opportunities", score: 4 },
    ],
  },
  {
    id: "loss_tolerance",
    text: "If your portfolio dropped 20% in a month, what would you do?",
    dimension: "volatility",
    options: [
      { label: "Sell everything immediately to cut losses", score: 1 },
      { label: "Sell some positions and hold the rest", score: 2 },
      { label: "Hold everything and wait for recovery", score: 3 },
      { label: "Buy more at lower prices — it's an opportunity", score: 4 },
    ],
  },
  {
    id: "time_horizon",
    text: "What is your primary investment time horizon?",
    dimension: "horizon",
    options: [
      { label: "Short-term — less than 1 year", score: 1 },
      { label: "Medium-term — 1 to 3 years", score: 2 },
      { label: "Long-term — 3 to 7 years", score: 3 },
      { label: "Very long-term — 7+ years (retirement planning)", score: 4 },
    ],
  },
  {
    id: "investment_goal",
    text: "What is your primary investment goal?",
    dimension: "general",
    options: [
      { label: "Capital preservation — protect my money from inflation", score: 1 },
      { label: "Regular income — dividends and steady returns", score: 2 },
      { label: "Balanced growth — grow wealth steadily over time", score: 3 },
      { label: "Aggressive growth — maximize returns even with higher risk", score: 4 },
    ],
  },
  {
    id: "income_stability",
    text: "How stable is your current income?",
    dimension: "general",
    options: [
      { label: "Irregular / freelance — income varies month to month", score: 1 },
      { label: "Mostly stable with some variability (commissions, bonuses)", score: 2 },
      { label: "Stable salary with reliable monthly income", score: 3 },
      { label: "Very stable with significant surplus savings each month", score: 4 },
    ],
  },
  {
    id: "emergency_fund",
    text: "Do you have an emergency fund?",
    dimension: "general",
    options: [
      { label: "No emergency fund", score: 1 },
      { label: "Less than 3 months of expenses", score: 2 },
      { label: "3 to 6 months of expenses", score: 3 },
      { label: "More than 6 months of expenses", score: 4 },
    ],
  },
  {
    id: "concentration",
    text: "How do you feel about portfolio concentration?",
    dimension: "volatility",
    options: [
      { label: "I want broad diversification across many stocks and sectors", score: 1 },
      { label: "Moderate diversification — 10-15 stocks across key sectors", score: 2 },
      { label: "Focused portfolio — 5-10 high-conviction stocks", score: 3 },
      { label: "Concentrated bets — a few stocks I strongly believe in", score: 4 },
    ],
  },
  {
    id: "investable_surplus",
    text: "What is your approximate monthly investable surplus?",
    dimension: "general",
    options: [
      { label: "Under \u20B910,000", score: 1 },
      { label: "\u20B910,000 - \u20B950,000", score: 2 },
      { label: "\u20B950,000 - \u20B91,00,000", score: 3 },
      { label: "Over \u20B91,00,000", score: 4 },
    ],
  },
  {
    id: "sector_preference",
    text: "Which types of stocks interest you most?",
    dimension: "general",
    options: [
      { label: "Blue-chip large caps — HDFC, Reliance, TCS", score: 1 },
      { label: "A mix of large caps and proven mid caps", score: 2 },
      { label: "Growth-oriented mid and small caps with potential", score: 3 },
      { label: "Emerging themes — new-age tech, green energy, speciality chemicals", score: 4 },
    ],
  },
];

// Max possible score: 11 questions * 4 = 44
// Conservative: <= 20, Moderate: 21-32, Aggressive: >= 33
function getRiskProfile(score: number): string {
  if (score <= 20) return "conservative";
  if (score <= 32) return "moderate";
  return "aggressive";
}

function getRiskLabel(profile: string): string {
  switch (profile) {
    case "conservative":
      return "Conservative";
    case "moderate":
      return "Moderate";
    case "aggressive":
      return "Aggressive";
    default:
      return profile;
  }
}

function getRiskColor(profile: string): string {
  switch (profile) {
    case "conservative":
      return "text-blue-400";
    case "moderate":
      return "text-yellow-400";
    case "aggressive":
      return "text-red-400";
    default:
      return "text-foreground";
  }
}

function getRiskDescription(profile: string): string {
  switch (profile) {
    case "conservative":
      return "We will recommend a portfolio focused on stability with blue-chip stocks and lower volatility. Signals will be filtered for higher confidence, and position sizing will be cautious.";
    case "moderate":
      return "We will recommend a balanced portfolio mixing growth and value stocks. Signals are shown with standard thresholds, and position sizing is moderate.";
    case "aggressive":
      return "We will recommend a growth-oriented portfolio with higher return potential. All signal types are shown prominently, and position sizing allows for larger concentrated bets.";
    default:
      return "";
  }
}

function computeSubScores(answers: Record<string, number>) {
  let volatility = 0;
  let horizon = 0;
  let knowledge = 0;
  let volCount = 0;
  let horCount = 0;
  let knCount = 0;

  for (const q of questions) {
    const score = answers[q.id];
    if (score === undefined) continue;
    switch (q.dimension) {
      case "volatility":
        volatility += score;
        volCount++;
        break;
      case "horizon":
        horizon += score;
        horCount++;
        break;
      case "knowledge":
        knowledge += score;
        knCount++;
        break;
    }
  }

  return {
    volatility_tolerance: volCount > 0 ? Math.round((volatility / volCount) * 25) : 0,
    time_horizon_score: horCount > 0 ? Math.round((horizon / horCount) * 25) : 0,
    knowledge_score: knCount > 0 ? Math.round((knowledge / knCount) * 25) : 0,
  };
}

function getInvestableSurplusRange(answers: Record<string, number>): string {
  const score = answers["investable_surplus"];
  switch (score) {
    case 1:
      return "under_10k";
    case 2:
      return "10k_50k";
    case 3:
      return "50k_1l";
    case 4:
      return "over_1l";
    default:
      return "unknown";
  }
}

export default function OnboardingPage() {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();
  const { user, loading } = useAuth();

  const currentQuestion = questions[step];
  const isComplete = step >= questions.length;
  const totalScore = Object.values(answers).reduce((a, b) => a + b, 0);
  const riskProfile = getRiskProfile(totalScore);

  function selectAnswer(score: number) {
    setAnswers((prev) => ({ ...prev, [currentQuestion.id]: score }));
  }

  function next() {
    if (answers[currentQuestion.id] === undefined) {
      toast.error("Please select an option");
      return;
    }
    setStep((s) => s + 1);
  }

  function prev() {
    setStep((s) => Math.max(0, s - 1));
  }

  async function handleSubmit() {
    setSubmitting(true);
    try {
      const total = Object.values(answers).reduce((a, b) => a + b, 0);
      const risk_profile = getRiskProfile(total);
      const subScores = computeSubScores(answers);
      const investable_surplus_range = getInvestableSurplusRange(answers);

      const supabase = createClient();

      const {
        data: { user: currentUser },
      } = await supabase.auth.getUser();
      const userId = currentUser?.id;
      if (!userId) throw new Error("Not authenticated");

      const { error } = await supabase
        .from("profiles")
        .update({
          risk_score: total,
          risk_profile,
          onboarding_complete: true,
          volatility_tolerance: subScores.volatility_tolerance,
          time_horizon_score: subScores.time_horizon_score,
          knowledge_score: subScores.knowledge_score,
          investable_surplus_range,
        })
        .eq("id", userId);

      if (error) throw new Error(error.message);

      toast.success("Risk profile saved!");
      router.push("/dashboard");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to save profile";
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
            <TrendingUp className="h-6 w-6 text-primary" />
          </div>
          <CardTitle className="text-2xl">Risk Assessment</CardTitle>
          <CardDescription>
            {isComplete
              ? "Your risk profile is ready"
              : `Question ${step + 1} of ${questions.length}`}
          </CardDescription>
        </CardHeader>

        <CardContent>
          <Progress
            value={isComplete ? 100 : (step / questions.length) * 100}
            className="mb-6"
          />

          {!isComplete ? (
            <div className="space-y-4">
              <h3 className="text-lg font-medium">{currentQuestion.text}</h3>
              <div className="space-y-2">
                {currentQuestion.options.map((opt) => (
                  <button
                    key={opt.score}
                    type="button"
                    onClick={() => selectAnswer(opt.score)}
                    className={`w-full rounded-lg border p-4 text-left text-sm transition-colors ${
                      answers[currentQuestion.id] === opt.score
                        ? "border-primary bg-primary/10 text-foreground"
                        : "border-border bg-card hover:border-muted-foreground/30"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6 text-center">
              <div>
                <p className="text-sm text-muted-foreground">
                  Based on your answers, your risk profile is
                </p>
                <p
                  className={`mt-2 text-3xl font-bold ${getRiskColor(riskProfile)}`}
                >
                  {getRiskLabel(riskProfile)}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Score: {totalScore} / {questions.length * 4}
                </p>
              </div>

              {/* Sub-scores breakdown */}
              <div className="mx-auto grid max-w-xs gap-3 text-left">
                {(() => {
                  const sub = computeSubScores(answers);
                  return (
                    <>
                      <div>
                        <div className="flex justify-between text-xs text-muted-foreground mb-1">
                          <span>Volatility Tolerance</span>
                          <span>{sub.volatility_tolerance}/100</span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-muted">
                          <div
                            className="h-full bg-blue-500 transition-all"
                            style={{ width: `${sub.volatility_tolerance}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-xs text-muted-foreground mb-1">
                          <span>Time Horizon</span>
                          <span>{sub.time_horizon_score}/100</span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-muted">
                          <div
                            className="h-full bg-purple-500 transition-all"
                            style={{ width: `${sub.time_horizon_score}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-xs text-muted-foreground mb-1">
                          <span>Market Knowledge</span>
                          <span>{sub.knowledge_score}/100</span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-muted">
                          <div
                            className="h-full bg-amber-500 transition-all"
                            style={{ width: `${sub.knowledge_score}%` }}
                          />
                        </div>
                      </div>
                    </>
                  );
                })()}
              </div>

              <p className="text-sm text-muted-foreground">
                {getRiskDescription(riskProfile)}
              </p>
            </div>
          )}
        </CardContent>

        <CardFooter className="flex justify-between gap-3">
          {!isComplete ? (
            <>
              <Button
                variant="outline"
                onClick={prev}
                disabled={step === 0}
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Back
              </Button>
              <Button onClick={next}>
                {step < questions.length - 1 ? (
                  <>
                    Next
                    <ChevronRight className="ml-1 h-4 w-4" />
                  </>
                ) : (
                  "See Results"
                )}
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={() => setStep(0)}>
                Retake
              </Button>
              <Button onClick={handleSubmit} disabled={submitting || loading || !user}>
                {submitting ? "Saving..." : "Continue to Dashboard"}
              </Button>
            </>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
