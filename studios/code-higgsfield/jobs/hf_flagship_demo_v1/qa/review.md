# QA Protocol Review — `hf_flagship_demo_v1`

- **Verdict:** `ACCEPT` (98/100)
- **Artifact:** `master_60fps.mp4` (1080x1920 @ 60.0 FPS, 10.114s, 606 frames)
- **Contact Sheet:** `qa/contact_sheet.png`

## Fixed Gates Summary
1. **Integrity & Spec:** `PASS` (1080x1920, `yuv420p`, Audio=True)
2. **Holds & Shot Density:** `PASS` (0 freezes, 4.94 shots/10s)
3. **Hook & Motion Causality:** `PASS` (First 0.5s motion=1.964, mean diff=1.239)
4. **Typography Safe Area & WCAG:** `PASS` (Margin=8.0%, Contrast=19.02:1)
5. **Sound Loudness (EBU R128):** `PASS` (Integrated=-13.7 LUFS, True Peak=-1.2 dBFS)
