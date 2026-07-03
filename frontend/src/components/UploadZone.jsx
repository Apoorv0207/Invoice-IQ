import { useState, useRef } from 'react'
import { Upload, FileText, X, CheckCircle, Loader } from 'lucide-react'
import { uploadInvoice, uploadBatch } from '../utils/api'
import clsx from 'clsx'

export default function UploadZone({ onUploadComplete }) {
  const [dragging, setDragging] = useState(false)
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [results, setResults] = useState([])
  const inputRef = useRef(null)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const dropped = Array.from(e.dataTransfer.files).filter(f =>
      ['application/pdf', 'image/jpeg', 'image/png', 'image/webp'].includes(f.type)
    )
    setFiles(prev => [...prev, ...dropped])
  }

  const handleFileInput = (e) => {
    const selected = Array.from(e.target.files)
    setFiles(prev => [...prev, ...selected])
  }

  const removeFile = (idx) => {
    setFiles(prev => prev.filter((_, i) => i !== idx))
  }

  const handleUpload = async () => {
    if (!files.length) return
    setUploading(true)
    setResults([])

    try {
      if (files.length === 1) {
        const result = await uploadInvoice(files[0])
        setResults([{ file: files[0].name, ...result }])
      } else {
        const result = await uploadBatch(files)
        setResults(result.invoices || [])
      }
      setFiles([])
      if (onUploadComplete) onUploadComplete()
    } catch (err) {
      setResults([{ error: err.message }])
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={clsx(
          'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all',
          dragging
            ? 'border-brand-500 bg-brand-500/5'
            : 'border-slate-700 hover:border-slate-600 hover:bg-slate-800/50'
        )}
      >
        <Upload className="mx-auto mb-3 text-slate-500" size={32} />
        <p className="text-slate-300 font-medium">Drop invoices here or click to browse</p>
        <p className="text-slate-500 text-sm mt-1">PDF, JPEG, PNG, WebP · Max 10MB each · Up to 20 files</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.jpg,.jpeg,.png,.webp"
          className="hidden"
          onChange={handleFileInput}
        />
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file, idx) => (
            <div key={idx} className="flex items-center gap-3 bg-slate-800 rounded-lg px-3 py-2">
              <FileText size={16} className="text-brand-400 shrink-0" />
              <span className="text-sm text-slate-300 flex-1 truncate">{file.name}</span>
              <span className="text-xs text-slate-500">{(file.size / 1024).toFixed(0)} KB</span>
              <button onClick={() => removeFile(idx)} className="text-slate-500 hover:text-red-400 transition-colors">
                <X size={14} />
              </button>
            </div>
          ))}

          <button
            onClick={handleUpload}
            disabled={uploading}
            className="btn-primary w-full flex items-center justify-center gap-2 py-2.5"
          >
            {uploading
              ? <><Loader size={16} className="animate-spin" /> Processing...</>
              : <><Upload size={16} /> Upload {files.length} Invoice{files.length > 1 ? 's' : ''}</>
            }
          </button>
        </div>
      )}

      {/* Upload Results */}
      {results.length > 0 && (
        <div className="space-y-2">
          {results.map((r, idx) => (
            <div key={idx} className={clsx(
              'flex items-center gap-2 text-sm rounded-lg px-3 py-2',
              r.error ? 'bg-red-500/10 text-red-400' : 'bg-emerald-500/10 text-emerald-400'
            )}>
              <CheckCircle size={14} />
              {r.error
                ? `Error: ${r.error}`
                : `${r.file_name || r.file} → queued for processing`
              }
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
