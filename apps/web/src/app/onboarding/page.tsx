"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { apiFetch } from "@/lib/api";
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
  options: { label: string; score: number }[];
}

const questions: Question[] = [
  {
    id: "experience",
    text: "What is your investment experience?",
    options: [
      { label: "New to investing (less than 1 year)", score: 1 },
      { label: "Some experience (1-5 years)", score: 2 },
      { label: "Experienced investor (5+ years)", score: 3 },
    ],
  },
  {
    id: "risk_tolerance",
    text: "How would you describe your risk tolerance?",
    options: [
      { label: "I prefer safety over returns", score: 1 },
      { label: "I can accept moderate risk for moderate returns", score: 2 },
      { label: "I am comfortable with high risk for high returns", score: 3 },
    ],
  },
  {
    id: "time_horizon",
    text: "What is your investment time horizon?",
    options: [
      { label: "Short-term (less than 2 years)", score: 1 },
      { label: "Medium-term (2-7 years)", score: 2 },
      { label: "Long-term (7+ years)", score: 3 },
    ],
  },
  {
    id: "loss_tolerance",
    text: "If your portfolio dropped 20% in a month, what would you do?",
    options: [
      { label: "Sell everything immediately", score: 1 },
      { label: "Hold and wait for recovery", score: 2 },
      { label: "Buy more at lower prices", score: 3 },
    ],
  },
  {
    id: "income_stability",
    text: "How stable is your income?",
    options: [
      { label: "Irregular / freelance income", score: 1 },
      { label: "Stable salary with some variability", score: 2 },
      { label: "Very stable with surplus savings", score: 3 },
    ],
  },
];

function getRiskProfile(score: number): string {
  if (score <= 8) return "conservative";
  if (score <= 11) return "moderate";
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

export default function OnboardingPage() {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();

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
      await apiFetch("/profile/risk", {
        method: "PUT",
        body: JSON.stringify({
          risk_score: totalScore,
          risk_profile: riskProfile,
          answers,
        }),
      });
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
                  Score: {totalScore} / 15
                </p>
              </div>
              <p className="text-sm text-muted-foreground">
                {riskProfile === "conservative" &&
                  "We will recommend a portfolio focused on stability with blue-chip stocks and lower volatility."}
                {riskProfile === "moderate" &&
                  "We will recommend a balanced portfolio mixing growth and value stocks."}
                {riskProfile === "aggressive" &&
                  "We will recommend a growth-oriented portfolio with higher return potential."}
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
              <Button onClick={handleSubmit} disabled={submitting}>
                {submitting ? "Saving..." : "Continue to Dashboard"}
              </Button>
            </>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
