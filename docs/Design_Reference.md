# Design Reference

## Aesthetic
Dark, terminal-meets-premium. Same language as SentinelAI V2.
NOT: default Streamlit blue, light backgrounds, rounded pastel cards.
YES: near-black backgrounds, monospace for technical output, 
     gold/amber accents for primary actions, subtle borders.

## Color palette
Background: #0d0d0d
Surface: #141414
Border: #2a2a2a
Primary accent: #c9a84c (gold)
Text primary: #e8e8e8
Text secondary: #888888
Monospace: JetBrains Mono
Body: Inter

## Streamlit custom CSS target
st.markdown("""<style>
  .stApp { background: #0d0d0d; }
  .stButton > button { background: #c9a84c; color: #0d0d0d; 
                       font-family: 'JetBrains Mono'; border: none; }
</style>""", unsafe_allow_html=True)

## Page structure
Left panel (30%): file uploads, passphrase input, action button
Right panel (70%): output preview, technical metadata 
  (capacity used, PSNR score, detection probability, download button)

## CLI output style
Use rich panels for results. Green for success, red for failure, 
yellow for warnings. Monospace table for technical stats.

## Steganalysis Results Panel
- Appears in the right panel after embed or analyze operations
- Layout: 3-column metric cards (Chi-squared score, SSIM score, RS score)
- Each card shows: metric name (monospace, #888), value (large, JetBrains Mono), status bar (colored)
- Verdict badge: SAFE (green #22c55e background), MODERATE (yellow #eab308), HIGH RISK (red #ef4444)
- Below cards: expandable technical details accordion

## Steganographic Diff Viewer
- Side-by-side: Cover image | Stego image
- Toggle buttons: Normal View | Bit-Plane 0 | Bit-Plane 1 | Enhanced Diff
- Enhanced diff: amplified pixel difference map (x50 gain) with heatmap colormap
- Below images: histogram comparison (cover vs stego pixel distributions)

## Batch Processing UI
- Directory selector or drag-drop zone for multiple files
- File list table: filename, size, carrier type, status (pending/processing/done/error)
- Progress bar per file + overall progress bar
- Results summary: N succeeded, N failed, average PSNR, average detection score

## Error States
- Wrong passphrase: red banner with lock icon, 'Integrity check failed — wrong passphrase or corrupted file'
- Capacity exceeded: yellow banner with warning icon, show required vs available bytes
- Unsupported format: gray banner, 'Supported formats: PNG, JPEG, MP3'
- Processing errors: red toast notification, auto-dismiss after 5s

## Loading States
- Embed/extract: pulsing gold progress bar with 'Embedding payload...' / 'Extracting payload...' text
- Analysis: spinning radar animation with 'Running steganalysis...'
- Batch: per-file progress bars stacked vertically

## Toast Notifications
- Success: dark green (#0a3622) background, white text, check icon, 'Payload embedded successfully'
- Error: dark red (#3b0f0f) background, white text, X icon
- Info: dark blue (#0f2b3b) background, white text, info icon
- Position: bottom-right, stacked, auto-dismiss 5s