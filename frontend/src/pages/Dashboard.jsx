import { useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";
import { toast } from "sonner";
import {
  Home,
  Upload,
  History,
  Settings,
  LogOut,
  ScanFace,
  CloudUpload,
  FileImage,
  FileVideo,
  AlertTriangle,
  CheckCircle,
  Loader2,
  X,
  Trash2,
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Progress } from "../components/ui/progress";
import { ScrollArea } from "../components/ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
const API = `${BACKEND_URL}/api`;

// Sidebar navigation
const navItems = [
  { icon: Home, label: "Dashboard", id: "dashboard" },
  { icon: Upload, label: "Upload", id: "upload" },
  { icon: History, label: "History", id: "history" },
  { icon: Settings, label: "Settings", id: "settings" },
];

// Confidence Ring Component
const ConfidenceRing = ({ confidence, isFake }) => {
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const progress = circumference; // Full ring fill
  const color = isFake ? "#F43F5E" : "#10B981";

  return (
    <div className="relative w-40 h-40">
      <svg className="w-full h-full result-ring" viewBox="0 0 140 140">
        {/* Background ring */}
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="8"
        />
        {/* Progress ring */}
        <motion.circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference - progress }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          style={{ filter: `drop-shadow(0 0 10px ${color})` }}
        />
      </svg>
      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.5, type: "spring" }}
          className="text-3xl font-black font-[Outfit]"
          style={{ color: color }}
        >
          {isFake ? "FAKE" : "REAL"}
        </motion.span>
      </div>
    </div>
  );
};

// Result Card Component
const ResultCard = ({ result, onClear }) => {
  const isFake = result.is_fake;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass rounded-2xl p-6 tracing-beam"
      data-testid="result-card"
    >
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-xl font-bold text-white font-[Outfit]">Analysis Result</h3>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClear}
          className="text-zinc-400 hover:text-white"
          data-testid="clear-result-button"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>

      <div className="flex flex-col md:flex-row items-center gap-6">
        {/* Confidence Ring */}
        <ConfidenceRing confidence={result.confidence} isFake={isFake} />

        {/* Result details */}
        <div className="flex-1 space-y-4">
          {/* Verdict */}
          <motion.div
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className={`flex items-center gap-3 p-4 rounded-xl ${
              isFake
                ? "bg-rose-500/10 border border-rose-500/30"
                : "bg-emerald-500/10 border border-emerald-500/30"
            }`}
            data-testid="verdict-indicator"
          >
            {isFake ? (
              <AlertTriangle className="w-6 h-6 text-rose-400" />
            ) : (
              <CheckCircle className="w-6 h-6 text-emerald-400" />
            )}
            <div>
              <span
                className={`text-lg font-bold ${
                  isFake ? "text-rose-400" : "text-emerald-400"
                }`}
              >
                {isFake ? "LIKELY FAKE" : "LIKELY AUTHENTIC"}
              </span>
              <p className="text-xs text-zinc-400">
                {isFake
                  ? "AI-generated or manipulated content detected"
                  : "No significant manipulation indicators found"}
              </p>
            </div>
          </motion.div>

          {/* Analysis text */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <h4 className="text-sm text-zinc-400 mb-2 font-mono">ANALYSIS</h4>
            <p className="text-zinc-300 text-sm leading-relaxed" data-testid="analysis-text">
              {result.analysis}
            </p>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
};

// History Item Component
const HistoryItem = ({ item, onClick }) => {
  const isFake = item.is_fake;

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      onClick={onClick}
      className="relative cursor-pointer group"
      data-testid="history-item"
    >
      <div className="aspect-square rounded-xl overflow-hidden glass border border-white/10 group-hover:border-cyan-500/30 transition-colors">
        {item.preview ? (
          <img
            src={item.preview}
            alt="Analysis thumbnail"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-zinc-900">
            <FileImage className="w-8 h-8 text-zinc-600" />
          </div>
        )}
        {/* Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        {/* Badge */}
        <div
          className={`absolute top-2 right-2 px-2 py-1 rounded-full text-[10px] font-mono font-bold ${
            isFake
              ? "bg-rose-500/80 text-white"
              : "bg-emerald-500/80 text-white"
          }`}
        >
          {isFake ? "FAKE" : "REAL"}
        </div>
        {/* Confidence */}
        <div className="absolute bottom-2 left-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <span className="text-xs text-white font-mono">
            Verdict: {isFake ? "FAKE" : "REAL"}
          </span>
        </div>
      </div>
    </motion.div>
  );
};

const Dashboard = ({ user, setUser }) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);

  const handleLogout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
    } catch (e) {
      // Ignore errors
    }
    setUser(null);
    navigate("/login", { replace: true });
  };

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  }, []);

  const handleFileSelect = (file) => {
    // Validate file type
    const validTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp", "video/mp4", "video/webm"];
    if (!validTypes.includes(file.type)) {
      toast.error("Invalid file type. Please upload JPG, PNG, WEBP, MP4, or WEBM files.");
      return;
    }

    // Validate file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      toast.error("File too large. Maximum size is 50MB.");
      return;
    }

    setUploadedFile(file);
    setAnalysisResult(null);

    // Create preview
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleFileInput = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleUploadAndAnalyze = async () => {
    if (!uploadedFile) return;

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Upload file
      const formData = new FormData();
      formData.append("file", uploadedFile);

      const uploadResponse = await axios.post(`${API}/upload`, formData, {
        withCredentials: true,
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        },
      });

      setIsUploading(false);
      setIsAnalyzing(true);

      // Analyze file
      const analysisResponse = await axios.post(
        `${API}/analyze`,
        {
          storage_path: uploadResponse.data.storage_path,
          file_type: uploadResponse.data.file_type,
        },
        { withCredentials: true }
      );

      setAnalysisResult(analysisResponse.data);

      // Add to history
      setHistory((prev) => [
        {
          id: analysisResponse.data.id,
          preview: previewUrl,
          is_fake: analysisResponse.data.is_fake,
          analysis: analysisResponse.data.analysis,
          created_at: analysisResponse.data.created_at,
        },
        ...prev,
      ]);

      toast.success("Analysis complete!");
    } catch (error) {
      console.error("Upload/analysis error:", error);
      toast.error(error.response?.data?.detail || "Analysis failed. Please try again.");
    } finally {
      setIsUploading(false);
      setIsAnalyzing(false);
    }
  };

  const clearUpload = () => {
    setUploadedFile(null);
    setPreviewUrl(null);
    setAnalysisResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const clearHistory = () => {
    setHistory([]);
    toast.success("History cleared");
  };

  return (
    <TooltipProvider>
      <div className="dashboard-layout" data-testid="dashboard">
        {/* Sidebar */}
        <motion.aside
          initial={{ x: -100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          className="sidebar glass border-r border-white/10"
        >
          <div className="h-full flex flex-col p-4">
            {/* Logo */}
            <div className="flex items-center gap-2 mb-8 px-2">
              <ScanFace className="w-8 h-8 text-cyan-400 flex-shrink-0" />
              <span className="text-lg font-bold text-white font-[Outfit] hidden lg:block">
                True<span className="text-cyan-400">Pixel</span>
              </span>
            </div>

            {/* Nav items */}
            <nav className="flex-1 space-y-2">
              {navItems.map((item) => (
                <Tooltip key={item.id}>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => setActiveTab(item.id)}
                      className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 ${
                        activeTab === item.id
                          ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
                          : "text-zinc-400 hover:text-white hover:bg-white/5"
                      }`}
                      data-testid={`nav-${item.id}`}
                    >
                      <item.icon className="w-5 h-5 flex-shrink-0" />
                      <span className="hidden lg:block text-sm font-medium">
                        {item.label}
                      </span>
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right" className="lg:hidden">
                    {item.label}
                  </TooltipContent>
                </Tooltip>
              ))}
            </nav>

            {/* User menu */}
            <div className="pt-4 border-t border-white/10">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button
                    className="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-zinc-400 hover:text-white hover:bg-white/5 transition-colors"
                    data-testid="user-menu-trigger"
                  >
                    <img
                      src={user?.picture || "https://via.placeholder.com/40"}
                      alt={user?.name}
                      className="w-8 h-8 rounded-full flex-shrink-0"
                    />
                    <div className="hidden lg:block text-left flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {user?.name}
                      </p>
                      <p className="text-xs text-zinc-500 truncate">{user?.email}</p>
                    </div>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56 glass border-white/10">
                  <div className="px-3 py-2 lg:hidden">
                    <p className="text-sm font-medium text-white">{user?.name}</p>
                    <p className="text-xs text-zinc-500">{user?.email}</p>
                  </div>
                  <DropdownMenuSeparator className="lg:hidden bg-white/10" />
                  <DropdownMenuItem
                    onClick={handleLogout}
                    className="text-rose-400 focus:text-rose-400 focus:bg-rose-500/10"
                    data-testid="logout-button"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </motion.aside>

        {/* Main content */}
        <main className="main-content">
          <AnimatePresence mode="wait">
            {/* Dashboard / Upload view */}
            {(activeTab === "dashboard" || activeTab === "upload") && (
              <motion.div
                key="upload"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {/* Header */}
                <div>
                  <h1 className="text-3xl font-black text-white font-[Outfit]">
                    Deepfake Detection
                  </h1>
                  <p className="text-zinc-400 text-sm mt-1 font-mono">
                    Upload an image or video to analyze for AI manipulation
                  </p>
                </div>

                {/* Upload zone */}
                <motion.div
                  animate={{ y: [-3, 3, -3] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                  className={`upload-zone rounded-2xl p-8 transition-all duration-300 ${
                    isDragging ? "drag-over border-cyan-400" : ""
                  } ${uploadedFile ? "border-cyan-500/50" : ""}`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  data-testid="upload-dropzone"
                >
                  {!uploadedFile ? (
                    <div className="text-center">
                      <motion.div
                        animate={{ scale: isDragging ? 1.1 : 1 }}
                        className="mb-4"
                      >
                        <CloudUpload className="w-16 h-16 mx-auto text-cyan-400 opacity-50" />
                      </motion.div>
                      <h3 className="text-lg font-semibold text-white mb-2">
                        Drag & drop your file here
                      </h3>
                      <p className="text-zinc-500 text-sm mb-4">
                        or click to browse
                      </p>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/jpeg,image/jpg,image/png,image/webp,video/mp4,video/webm"
                        onChange={handleFileInput}
                        className="hidden"
                        id="file-input"
                        data-testid="file-input"
                      />
                      <Button
                        onClick={() => fileInputRef.current?.click()}
                        className="bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 border border-cyan-500/30"
                        data-testid="browse-files-button"
                      >
                        Browse Files
                      </Button>
                      <p className="text-zinc-600 text-xs mt-4">
                        Supports JPG, PNG, WEBP, MP4, WEBM (max 50MB)
                      </p>
                    </div>
                  ) : (
                    <div className="flex flex-col md:flex-row items-center gap-6">
                      {/* Preview */}
                      <div className="relative w-48 h-48 rounded-xl overflow-hidden flex-shrink-0 glass">
                        {uploadedFile.type.startsWith("image") ? (
                          <img
                            src={previewUrl}
                            alt="Preview"
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <video
                            src={previewUrl}
                            className="w-full h-full object-cover"
                          />
                        )}
                        <button
                          onClick={clearUpload}
                          className="absolute top-2 right-2 p-1.5 rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
                          data-testid="clear-upload-button"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      {/* File info & actions */}
                      <div className="flex-1 text-center md:text-left">
                        <div className="flex items-center gap-2 mb-2 justify-center md:justify-start">
                          {uploadedFile.type.startsWith("image") ? (
                            <FileImage className="w-5 h-5 text-cyan-400" />
                          ) : (
                            <FileVideo className="w-5 h-5 text-purple-400" />
                          )}
                          <span className="text-white font-medium truncate max-w-[200px]">
                            {uploadedFile.name}
                          </span>
                        </div>
                        <p className="text-zinc-500 text-sm mb-4">
                          {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>

                        {/* Progress or analyze button */}
                        {isUploading ? (
                          <div className="space-y-2">
                            <Progress value={uploadProgress} className="h-2" />
                            <p className="text-cyan-400 text-sm">
                              Uploading... {uploadProgress}%
                            </p>
                          </div>
                        ) : isAnalyzing ? (
                          <div className="flex items-center gap-2 text-purple-400">
                            <Loader2 className="w-5 h-5 animate-spin" />
                            <span>Analyzing with AI...</span>
                          </div>
                        ) : (
                          <Button
                            onClick={handleUploadAndAnalyze}
                            className="bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-400 hover:to-purple-400 text-white font-medium animate-pulse-glow"
                            data-testid="analyze-button"
                          >
                            <ScanFace className="w-4 h-4 mr-2" />
                            Analyze for Deepfake
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </motion.div>

                {/* Analysis result */}
                <AnimatePresence>
                  {analysisResult && (
                    <ResultCard result={analysisResult} onClear={clearUpload} />
                  )}
                </AnimatePresence>
              </motion.div>
            )}

            {/* History view */}
            {activeTab === "history" && (
              <motion.div
                key="history"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h1 className="text-3xl font-black text-white font-[Outfit]">
                      Analysis History
                    </h1>
                    <p className="text-zinc-400 text-sm mt-1 font-mono">
                      Your recent deepfake detection results (session only)
                    </p>
                  </div>
                  {history.length > 0 && (
                    <Button
                      variant="ghost"
                      onClick={clearHistory}
                      className="text-zinc-400 hover:text-rose-400"
                      data-testid="clear-history-button"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Clear History
                    </Button>
                  )}
                </div>

                {history.length === 0 ? (
                  <div className="glass rounded-2xl p-12 text-center">
                    <History className="w-16 h-16 mx-auto text-zinc-600 mb-4" />
                    <h3 className="text-lg font-semibold text-white mb-2">
                      No history yet
                    </h3>
                    <p className="text-zinc-500 text-sm">
                      Your analysis results will appear here
                    </p>
                  </div>
                ) : (
                  <div className="history-grid" data-testid="history-grid">
                    {history.map((item, index) => (
                      <motion.div
                        key={item.id}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <HistoryItem
                          item={item}
                          onClick={() => setAnalysisResult(item)}
                        />
                      </motion.div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {/* Settings view */}
            {activeTab === "settings" && (
              <motion.div
                key="settings"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                <div>
                  <h1 className="text-3xl font-black text-white font-[Outfit]">
                    Settings
                  </h1>
                  <p className="text-zinc-400 text-sm mt-1 font-mono">
                    Configure your TruePixel experience
                  </p>
                </div>

                <div className="glass rounded-2xl p-6 space-y-6">
                  {/* Account section */}
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4 font-[Outfit]">
                      Account
                    </h3>
                    <div className="flex items-center gap-4 p-4 bg-white/5 rounded-xl">
                      <img
                        src={user?.picture || "https://via.placeholder.com/60"}
                        alt={user?.name}
                        className="w-14 h-14 rounded-full"
                      />
                      <div>
                        <p className="text-white font-medium">{user?.name}</p>
                        <p className="text-zinc-500 text-sm">{user?.email}</p>
                      </div>
                    </div>
                  </div>

                  {/* About section */}
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4 font-[Outfit]">
                      About
                    </h3>
                    <div className="space-y-2 text-sm text-zinc-400">
                      <p>
                        <span className="text-zinc-500">Version:</span> 1.0.0
                      </p>
                      <p>
                        <span className="text-zinc-500">AI Model:</span> CNN + ViT Ensemble (GAN Detection)
                      </p>
                      <p>
                        <span className="text-zinc-500">Detection Types:</span> Images (Videos coming soon)
                      </p>
                    </div>
                  </div>

                  {/* Logout */}
                  <Button
                    variant="destructive"
                    onClick={handleLogout}
                    className="w-full"
                    data-testid="settings-logout-button"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign Out
                  </Button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </TooltipProvider>
  );
};

export default Dashboard;
