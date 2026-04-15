"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { useAuth } from "@/lib/auth-context";
import { apiFetch } from "@/lib/api";
import { toast } from "sonner";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { User, Shield, Moon, Sun, LogOut } from "lucide-react";

interface Profile {
  email: string;
  full_name: string;
  risk_profile: string;
  risk_score: number;
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

export default function SettingsPage() {
  const { user, signOut } = useAuth();
  const { theme, setTheme } = useTheme();
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = useCallback(async () => {
    try {
      const data = await apiFetch<Profile>("/profile");
      setProfile(data);
    } catch {
      // Profile might not exist yet
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  async function handleSignOut() {
    await signOut();
    router.push("/login");
  }

  const isDark = theme === "dark";

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Manage your account and preferences
        </p>
      </div>

      {/* Profile */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-4 w-4" />
            Profile
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? (
            <>
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-5 w-32" />
            </>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Email</p>
                  <p className="font-medium">{user?.email ?? "-"}</p>
                </div>
              </div>
              {profile?.full_name && (
                <div>
                  <p className="text-sm text-muted-foreground">Name</p>
                  <p className="font-medium">{profile.full_name}</p>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Risk Profile */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Risk Profile
          </CardTitle>
          <CardDescription>
            Your investment risk assessment results
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? (
            <Skeleton className="h-8 w-32" />
          ) : profile?.risk_profile ? (
            <>
              <div className="flex items-center gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">
                    Risk Profile
                  </p>
                  <p
                    className={`text-xl font-bold capitalize ${getRiskColor(profile.risk_profile)}`}
                  >
                    {profile.risk_profile}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Score</p>
                  <p className="text-xl font-bold">
                    {profile.risk_score} / 15
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                onClick={() => router.push("/onboarding")}
              >
                Retake Questionnaire
              </Button>
            </>
          ) : (
            <div className="space-y-2">
              <p className="text-muted-foreground">
                No risk profile set. Complete the questionnaire to get
                personalized recommendations.
              </p>
              <Button onClick={() => router.push("/onboarding")}>
                Take Risk Assessment
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Theme */}
      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {isDark ? (
                <Moon className="h-4 w-4" />
              ) : (
                <Sun className="h-4 w-4" />
              )}
              <div>
                <Label>Dark Mode</Label>
                <p className="text-xs text-muted-foreground">
                  Switch between dark and light theme
                </p>
              </div>
            </div>
            <Switch
              checked={isDark}
              onCheckedChange={(checked) =>
                setTheme(checked ? "dark" : "light")
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Sign Out */}
      <Card>
        <CardContent className="pt-6">
          <Button
            variant="destructive"
            className="w-full"
            onClick={handleSignOut}
          >
            <LogOut className="mr-2 h-4 w-4" />
            Sign Out
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
