"use client";

import { useCallback, useState } from "react";
import { Button, Card, CardHeader } from "@/components/ui";

interface ResumeUploadProps {
  onUploadComplete: (profile: unknown) => void;
  uploading: boolean;
  setUploading: (uploading: boolean) => void;
}

export function ResumeUpload({
  onUploadComplete,
  uploading,
  setUploading,
}: ResumeUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.endsWith(".pdf")) {
        setError("Please upload a PDF file");
        return;
      }

      setError(null);
      setFileName(file.name);
      setUploading(true);

      try {
        const { api } = await import("@/lib/api");
        const result = await api.uploadResume(file);
        if (result.success) {
          onUploadComplete(result.profile);
        } else {
          throw new Error("Upload failed");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to upload resume");
        setFileName(null);
      } finally {
        setUploading(false);
      }
    },
    [onUploadComplete, setUploading]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFile(e.dataTransfer.files[0]);
      }
    },
    [handleFile]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files[0]) {
        handleFile(e.target.files[0]);
      }
    },
    [handleFile]
  );

  return (
    <Card>
      <CardHeader
        title="Upload Your Resume"
        description="Upload your resume (PDF) to generate your artifact pack automatically"
      />

      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
            : "border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600"
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept=".pdf"
          onChange={handleChange}
          disabled={uploading}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
        />

        <div className="space-y-3">
          <div className="mx-auto w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
            <svg
              className="w-6 h-6 text-gray-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>

          {uploading ? (
            <div className="space-y-2">
              <div className="animate-spin mx-auto w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full" />
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Processing {fileName}...
              </p>
            </div>
          ) : fileName ? (
            <p className="text-sm text-green-600 dark:text-green-400">
              ✓ {fileName} uploaded
            </p>
          ) : (
            <>
              <p className="text-gray-600 dark:text-gray-400">
                <span className="font-medium text-blue-600 dark:text-blue-400">
                  Click to upload
                </span>{" "}
                or drag and drop
              </p>
              <p className="text-xs text-gray-500">PDF only, up to 10MB</p>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}
    </Card>
  );
}
