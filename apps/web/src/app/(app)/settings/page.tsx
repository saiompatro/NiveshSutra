"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { useAuth } from "@/lib/auth-context";
import {
  fetchProfile as fetchProfileApi,
  updateProfile as updateProfileApi,
} from "@/lib/api";
import type { Profile } from "@/lib/api";
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
import { User, Shield, Moon, Sun, LogOut, Bell } from "lucide-react";

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
  const [emailToggling, setEmailToggling] = useState(false);

  const loadProfile = useCallback(async () => {
    try {
      const data = await fetchProfileApi();
      setProfile(data);
    } catch {
      // Profile might not exist yet
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  async function handleSignOut() {
    await signOut();
    router.push("/login");
  }

  async function handleEmailToggle(checked: boolean) {
    setEmailToggling(true);
    try {
      await updateProfileApi({ email_notifications_enabled: checked } as any);
      setProfile((prev) =>
        prev ? { ...prev, email_notifications_enabled: checked } : prev
      );
      toast.success(
        checked ? "Email notifications enabled" : "Email notifications disabled"
      );
    } catch {
      toast.error("Failed to update notification settings");
    } finally {
      setEmailToggling(false);
    }
  }

  const isDark = theme === "dark";

  // Determine max score based on questionnaire version
  // New questionnaire: 11 questions * 4 = 44, Old: 5 * 3 = 15
  const maxScore =
    profile?.risk_score && profile.risk_score > 15 ? 44 : profile?.volatility_tolerance != null ? 44 : 15;

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
              <div className="flex items-center gap-6">
                <div>
                  <p className="text-sm text-muted-foreground">Risk Profile</p>
                  <p
                    className={`text-xl font-bold capitalize ${getRiskColor(profile.risk_profile)}`}
                  >
                    {profile.risk_profile}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Score</p>
                  <p className="text-xl font-bold">
                    {profile.risk_score} / {maxScore}
                  </p>
                </div>
              </div>

              {/* Sub-scores (only shown if expanded questionnaire was taken) */}
              {profile.volatility_tolerance != null && (
                <div className="space-y-3 pt-2">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Profile Breakdown
                  </p>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted-foreground">
                        Volatility Tolerance
                      </span>
                      <span>{profile.volatility_tolerance}/100</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full bg-blue-500 transition-all"
                        style={{
                          width: `${profile.volatility_tolerance}%`,
                        }}
                      />
                    </div>
                  </div>
                  {profile.time_horizon_score != null && (
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">
                          Time Horizon
                        </span>
                        <span>{profile.time_horizon_score}/100</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full bg-purple-500 transition-all"
                          style={{
                            width: `${profile.time_horizon_score}%`,
                          }}
                        />
                      </div>
                    </div>
                  )}
                  {profile.knowledge_score != null && (
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">
                          Market Knowledge
                        </span>
                        <span>{profile.knowledge_score}/100</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full bg-amber-500 transition-all"
                          style={{
                            width: `${profile.knowledge_score}%`,
                          }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}

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

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            Notifications
          </CardTitle>
          <CardDescription>
            Get notified when signals change for your accepted stocks
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div>
                <Label>Email Alerts</Label>
                <p className="text-xs text-muted-foreground">
                  Receive email when a tracked signal changes
                </p>
              </div>
            </div>
            <Switch
              checked={profile?.email_notifications_enabled ?? false}
              onCheckedChange={handleEmailToggle}
              disabled={emailToggling || loading}
            />
          </div>
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
