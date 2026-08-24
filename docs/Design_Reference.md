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