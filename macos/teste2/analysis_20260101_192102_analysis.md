# Análise de Qualidade de Vídeo

**Nome do Teste:** teste2

**Data:** 2026-01-01 19:27:35

---

## Métricas Objetivas e Subjetivas

| Vídeo | MOS | PSNR (dB) | SSIM |
|-------|-----|-----------|------|
| H264_500kbps.mp4 | 1.0 | 22.67 | 0.748 |
| H265_1000kbps.mp4 | 8.0 | 32.27 | 0.919 |
| H265_4000kbps.mp4 | 8.0 | 38.35 | 0.957 |
| H264_8000kbps.mp4 | 9.0 | 38.56 | 0.959 |
| H265_500kbps.mp4 | 3.0 | 27.43 | 0.856 |
| H264_1000kbps.mp4 | 2.0 | 26.71 | 0.834 |
| H265_2000kbps.mp4 | 8.0 | 35.99 | 0.944 |
| H264_4000kbps.mp4 | 7.0 | 35.83 | 0.941 |
| H265_8000kbps.mp4 | 10.0 | 40.00 | 0.966 |
| H264_2000kbps.mp4 | 7.0 | 31.97 | 0.906 |

## Correlações

| Métrica | Pearson | Spearman |
|---------|---------|----------|
| PSNR | 0.948 | 0.954 |
| SSIM | 0.949 | 0.954 |

## Modelos de Regressão

### PSNR → MOS

- **Linear:** MOS = 0.510 × PSNR + -10.528
- **R² Linear:** 0.899
- **Polinomial (grau 2):** MOS = -0.014 × PSNR² + 1.373 × PSNR + -23.765

### SSIM → MOS

- **Linear:** MOS = 42.326 × SSIM + -31.924
- **R² Linear:** 0.900
- **Polinomial (grau 2):** MOS = 127.925 × SSIM² + -178.835 × SSIM + 62.906

## Gráficos

![PSNR vs MOS](figures/psnr_vs_mos.png)

![SSIM vs MOS](figures/ssim_vs_mos.png)

![Comparação MOS vs PSNR](figures/mos_vs_psnr_comparison.png)

