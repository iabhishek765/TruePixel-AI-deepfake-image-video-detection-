import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ScanFace, Shield, Sparkles, Mail, Lock, User, Eye, EyeOff, ArrowRight, Loader2, Zap, Brain } from "lucide-react";
import { Button } from "../components/ui/button";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
const API = `${BACKEND_URL}/api`;

// Floating particles component
const Particles = () => {
  const particles = Array.from({ length: 30 }, (_, i) => ({
    id: i,
    size: Math.random() * 4 + 2,
    x: Math.random() * 100,
    duration: Math.random() * 20 + 15,
    delay: Math.random() * 10,
    opacity: Math.random() * 0.5 + 0.1,
  }));

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((p) => (
        <motion.div
          key={p.id}
          className="absolute rounded-full"
          style={{
            width: p.size,
            height: p.size,
            left: `${p.x}%`,
            background: `radial-gradient(circle, rgba(0, 240, 255, ${p.opacity}), transparent)`,
          }}
          animate={{
            y: [window.innerHeight, -50],
            opacity: [0, p.opacity, p.opacity, 0],
          }}
          transition={{
            duration: p.duration,
            delay: p.delay,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      ))}
    </div>
  );
};

const LoginPage = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [mode, setMode] = useState("login"); // "login" or "signup"
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");

  // Check existing session
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await axios.get(`${API}/auth/me`, {
          withCredentials: true,
        });
        if (response.data) {
          navigate("/dashboard", { replace: true });
        }
      } catch {
        // Not authenticated, stay on login
      }
      setIsLoading(false);
    };

    checkAuth();
  }, [navigate]);

  const handleInputChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      if (mode === "signup") {
        if (!formData.name.trim()) {
          setError("Name is required");
          setIsSubmitting(false);
          return;
        }
        if (!formData.email.trim()) {
          setError("Email is required");
          setIsSubmitting(false);
          return;
        }
        if (formData.password.length < 6) {
          setError("Password must be at least 6 characters");
          setIsSubmitting(false);
          return;
        }

        const response = await axios.post(
          `${API}/auth/register`,
          { name: formData.name, email: formData.email, password: formData.password },
          { withCredentials: true }
        );
        navigate("/dashboard", { state: { user: response.data }, replace: true });
      } else {
        if (!formData.email.trim()) {
          setError("Email is required");
          setIsSubmitting(false);
          return;
        }
        if (!formData.password.trim()) {
          setError("Password is required");
          setIsSubmitting(false);
          return;
        }

        const response = await axios.post(
          `${API}/auth/login`,
          { email: formData.email, password: formData.password },
          { withCredentials: true }
        );
        navigate("/dashboard", { state: { user: response.data }, replace: true });
      }
    } catch (err) {
      const message = err.response?.data?.detail || "Something went wrong. Please try again.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleMode = () => {
    setMode(prev => prev === "login" ? "signup" : "login");
    setError("");
    setFormData({ name: "", email: "", password: "" });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#05050A] flex items-center justify-center">
        <motion.div
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="text-cyan-400 font-mono"
        >
          Loading...
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#05050A] relative overflow-hidden" data-testid="login-page">
      {/* Background image */}
      <div 
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1773429494448-1c13750ad80d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxODh8MHwxfHNlYXJjaHwyfHxhYnN0cmFjdCUyMGRhcmslMjBuZW9uJTIwbmV0d29ya3xlbnwwfHx8fDE3NzQ1NDUyMDN8MA&ixlib=rb-4.1.0&q=85')`
        }}
      >
        <div className="absolute inset-0 bg-[#05050A]/80" />
      </div>

      {/* Particles */}
      <Particles />

      {/* Content */}
      <div className="relative z-10 min-h-screen flex items-center justify-center p-4">
        <div className="w-full max-w-5xl flex gap-8 items-center">
          
          {/* Left side — Features (hidden on mobile) */}
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, ease: "easeOut" }}
            className="hidden lg:flex flex-col flex-1 gap-6 pr-8"
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="relative">
                <ScanFace className="w-14 h-14 text-cyan-400" />
                <motion.div
                  className="absolute inset-0"
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <ScanFace className="w-14 h-14 text-cyan-400 blur-md" />
                </motion.div>
              </div>
              <h1 className="text-4xl font-black tracking-tight text-white font-[Outfit]">
                True<span className="text-cyan-400">Pixel</span>
              </h1>
            </div>
            
            <p className="text-zinc-400 text-lg leading-relaxed max-w-md">
              Detect AI-generated images and deepfakes with cutting-edge analysis powered by advanced vision models.
            </p>

            <div className="space-y-4 mt-4">
              {[
                { icon: Shield, title: "Deep Analysis", desc: "Multi-layer forensic examination of every pixel", color: "from-cyan-500 to-blue-600" },
                { icon: Brain, title: "GPT-5.2 Vision", desc: "State-of-the-art AI model for detection", color: "from-purple-500 to-pink-600" },
                { icon: Zap, title: "Instant Results", desc: "Get confidence scores in seconds", color: "from-amber-500 to-orange-600" },
                { icon: Sparkles, title: "High Accuracy", desc: "Trained on millions of real and synthetic images", color: "from-emerald-500 to-teal-600" },
              ].map((feature, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.1 }}
                  className="flex items-start gap-4 group"
                >
                  <div className={`flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                    <feature.icon className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-white font-semibold text-sm">{feature.title}</h3>
                    <p className="text-zinc-500 text-sm">{feature.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Right side — Login Card */}
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="w-full max-w-md mx-auto lg:mx-0"
          >
            <motion.div
              animate={{ y: [-3, 3, -3] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
              className="glass rounded-2xl p-8 tracing-beam"
            >
              {/* Mobile-only Logo */}
              <motion.div 
                className="flex items-center justify-center gap-3 mb-6 lg:hidden"
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <div className="relative">
                  <ScanFace className="w-10 h-10 text-cyan-400" />
                  <motion.div
                    className="absolute inset-0"
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <ScanFace className="w-10 h-10 text-cyan-400 blur-md" />
                  </motion.div>
                </div>
                <h1 className="text-2xl font-black tracking-tight text-white font-[Outfit]">
                  True<span className="text-cyan-400">Pixel</span>
                </h1>
              </motion.div>

              {/* Card Header */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.25 }}
                className="text-center mb-6"
              >
                <h2 className="text-xl font-bold text-white">
                  {mode === "login" ? "Welcome back" : "Create your account"}
                </h2>
                <p className="text-zinc-500 text-sm mt-1">
                  {mode === "login" ? "Sign in to continue analyzing media" : "Get started with deepfake detection"}
                </p>
              </motion.div>

              {/* Mode Toggle */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="flex rounded-xl overflow-hidden mb-6 border border-white/10 bg-white/[0.03]"
              >
                <button
                  type="button"
                  onClick={() => { setMode("login"); setError(""); }}
                  className={`flex-1 py-2.5 text-sm font-medium transition-all duration-300 ${
                    mode === "login"
                      ? "bg-cyan-500/20 text-cyan-400 border-b-2 border-cyan-400"
                      : "bg-transparent text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  onClick={() => { setMode("signup"); setError(""); }}
                  className={`flex-1 py-2.5 text-sm font-medium transition-all duration-300 ${
                    mode === "signup"
                      ? "bg-cyan-500/20 text-cyan-400 border-b-2 border-cyan-400"
                      : "bg-transparent text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  Sign Up
                </button>
              </motion.div>

              {/* Email/Password Form */}
              <motion.form
                onSubmit={handleSubmit}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.35 }}
                className="space-y-4"
              >
                <AnimatePresence mode="wait">
                  {mode === "signup" && (
                    <motion.div
                      key="name-field"
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <div className="relative group">
                        <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 group-focus-within:text-cyan-400 transition-colors" />
                        <input
                          id="name-input"
                          type="text"
                          name="name"
                          placeholder="Full Name"
                          value={formData.name}
                          onChange={handleInputChange}
                          className="w-full h-11 pl-10 pr-4 bg-white/5 border border-white/10 rounded-xl text-white text-sm placeholder:text-zinc-500 focus:outline-none focus:border-cyan-400/50 focus:bg-white/[0.07] transition-all duration-300"
                          autoComplete="name"
                        />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <div className="relative group">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 group-focus-within:text-cyan-400 transition-colors" />
                  <input
                    id="email-input"
                    type="email"
                    name="email"
                    placeholder="Email Address"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full h-11 pl-10 pr-4 bg-white/5 border border-white/10 rounded-xl text-white text-sm placeholder:text-zinc-500 focus:outline-none focus:border-cyan-400/50 focus:bg-white/[0.07] transition-all duration-300"
                    autoComplete="email"
                  />
                </div>

                <div className="relative group">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 group-focus-within:text-cyan-400 transition-colors" />
                  <input
                    id="password-input"
                    type={showPassword ? "text" : "password"}
                    name="password"
                    placeholder={mode === "signup" ? "Password (min 6 characters)" : "Password"}
                    value={formData.password}
                    onChange={handleInputChange}
                    className="w-full h-11 pl-10 pr-11 bg-white/5 border border-white/10 rounded-xl text-white text-sm placeholder:text-zinc-500 focus:outline-none focus:border-cyan-400/50 focus:bg-white/[0.07] transition-all duration-300"
                    autoComplete={mode === "signup" ? "new-password" : "current-password"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(prev => !prev)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>

                {/* Error message */}
                <AnimatePresence>
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -5 }}
                      className="flex items-center gap-2 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-red-400 flex-shrink-0" />
                      <p className="text-red-400 text-xs">{error}</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Submit button */}
                <Button
                  id="auth-submit-button"
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full h-11 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium rounded-xl flex items-center justify-center gap-2 transition-all duration-300 hover:shadow-[0_0_30px_rgba(0,200,255,0.3)] border-0"
                >
                  {isSubmitting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      {mode === "login" ? "Sign In" : "Create Account"}
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </Button>
              </motion.form>

              {/* Toggle mode link */}
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="text-center text-zinc-500 text-xs mt-6"
              >
                {mode === "login" ? "Don't have an account? " : "Already have an account? "}
                <button
                  type="button"
                  onClick={toggleMode}
                  className="text-cyan-400 hover:text-cyan-300 transition-colors font-medium"
                >
                  {mode === "login" ? "Sign up" : "Sign in"}
                </button>
              </motion.p>

              {/* Security note */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.55 }}
                className="flex items-center justify-center gap-1.5 mt-4"
              >
                <Shield className="w-3 h-3 text-emerald-500" />
                <span className="text-zinc-600 text-[10px] font-mono">Passwords encrypted with bcrypt</span>
              </motion.div>
            </motion.div>
          </motion.div>
        </div>
      </div>

      {/* Gradient orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
    </div>
  );
};

export default LoginPage;
