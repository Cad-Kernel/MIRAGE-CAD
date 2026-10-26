> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Review/04 Full Evaluation Results

Closure record: 2026-10-22. Status: CLOSED. Audit: PASS.

One paired training seed (42); 2500 fixed source IDs, four modalities, two arms. All eight gate and eight geometry runs were performed manually by the operator. This registrar only read artifacts and calculated CPU statistics; it did not run models or CAD programs.

## Definitions And Scope

A = STEP-first then balanced continuation; B = balanced from the start. Both plan branches ran actual4689+500 optimizer updates, with the same optimizer/scheduler reset and LR boundary. Each Stage4b ran actual1182 updates,3150 fixed-role rows x3 epochs. Shared upstreams/initialization/GT-plan Stage4 are unchanged. This changes cumulative modality exposure as well as its order; it is not a pure order-only ablation or a full-stack architecture comparison.

Syntax/Execute/Build/Solid/STEP export below come from standalone gate evaluation. Scoreable requires a readable reference, all five geometry-run gates, finite CD and F@1. Conditional metrics use each arm's own scoreable set. Paired geometry uses only the same jointly scoreable IDs. Unconditional F@1 uses all2500 cases, assigning zero to non-scoreable cases. F@1 is shown in percent in the main table; full distributions preserve raw0-1 fractions.

CD is0.5*mean(d(P,Q)^2)+0.5*mean(d(Q,P)^2), with no post-hoc rescaling/alignment/normalization. F@1 uses a distance threshold of1% of the target sampled-cloud bbox diagonal. Target NPZ clouds are downsampled to1024 with RandomState42 when needed; generated clouds are sampled by the native part API at1024 points, with no sampling seed exposed by this evaluator. Bbox error is mean absolute axis-extent error. Bbox ratio is generated/target sampled-cloud bbox diagonal. Preserve native units and distinguish this evaluation sampling from the fixed inference input cache.

No clipping, winsorization, outlier exclusion, target repair or row filtering was performed. CD>1000 is a retrospective inventory flag inherited from earlier revision summaries, not a threshold used for scoring, selection or significance. Exact case-level sign/McNemar tests below are descriptive, unadjusted for multiple comparisons, and do not measure training-seed uncertainty. Four modalities are not four independent training seeds.

## Complete Coverage And Primary Geometry

All coverage denominators are2500. CD/F@1 medians use the arm-specific scoreable subset.

| Modality | Arm | Syntax count (%) | Execute count (%) | Build count (%) | Solid count (%) | Export count (%) | Scoreable count (%) | Median CD | Median F@1 (%) | Unconditional mean F@1 (%) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| step | A | 2432 (97.28) | 1524 (60.96) | 1524 (60.96) | 1524 (60.96) | 1502 (60.08) | 1463 (58.52) | 3.14271984606 | 18.7976866883 | 10.7952394305 |
| step | B | 2087 (83.48) | 1447 (57.88) | 1447 (57.88) | 1447 (57.88) | 1384 (55.36) | 1325 (53.00) | 3.59055349289 | 14.5004734848 | 8.01502154386 |
| point | A | 2436 (97.44) | 1315 (52.60) | 1315 (52.60) | 1315 (52.60) | 1294 (51.76) | 1267 (50.68) | 56.2136549593 | 3.51291232639 | 2.38066315168 |
| point | B | 2064 (82.56) | 1358 (54.32) | 1358 (54.32) | 1358 (54.32) | 1256 (50.24) | 1188 (47.52) | 11.2261716224 | 5.26891637731 | 2.99142848349 |
| text | A | 2459 (98.36) | 1261 (50.44) | 1261 (50.44) | 1261 (50.44) | 1245 (49.80) | 1233 (49.32) | 4.39517460505 | 16.0132431402 | 7.8610994842 |
| text | B | 2124 (84.96) | 1348 (53.92) | 1348 (53.92) | 1348 (53.92) | 1295 (51.80) | 1192 (47.68) | 3.91862330554 | 15.592267745 | 7.4640015972 |
| image | A | 2426 (97.04) | 1352 (54.08) | 1352 (54.08) | 1352 (54.08) | 1321 (52.84) | 1283 (51.32) | 60.3670399429 | 4.06436011905 | 2.61800884729 |
| image | B | 2119 (84.76) | 1421 (56.84) | 1421 (56.84) | 1421 (56.84) | 1337 (53.48) | 1264 (50.56) | 8.39662810118 | 5.0771859976 | 3.06969489466 |

## Deltas B Minus A

Coverage/F@1 differences are percentage points; CD stays in native squared-distance units. Full-set conditional differences compare different arm-specific successful subsets; do not confuse them with paired differences.

| Modality | Syntax pp | Build pp | Export pp | Scoreable pp | Conditional median CD | Conditional median F@1 pp | Unconditional mean F@1 pp |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| step | -13.8 | -3.08 | -4.72 | -5.52 | 0.447833646835 | -4.29721320346 | -2.78021788661 |
| point | -14.88 | 1.72 | -1.52 | -3.16 | -44.9874833369 | 1.75600405093 | 0.610765331807 |
| text | -13.4 | 3.48 | 2 | -1.64 | -0.476551299501 | -0.420975395277 | -0.397097887 |
| image | -12.28 | 2.76 | 0.64 | -0.76 | -51.9704118417 | 1.01282587855 | 0.45168604737 |

## Jointly Scoreable Paired Geometry

All distributions are raw evaluator units (F@1 fractions, not percent). A/B medians in this table use identical IDs. Median(B-A) is not generally median(B)-median(A). Ties use absolute difference<=1e-12.

| Modality | Metric | N | A median | B median | Median paired B-A | B wins | A wins | Ties | Two-sided exact sign p |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| step | cd | 918 | 3.14417336119 | 3.75183308486 | 0.0173704793248 | 412 | 505 | 1 | 0.00236273494748 |
| step | f_score_1pct | 918 | 0.166501034007 | 0.163074242141 | -0.00494836832195 | 422 | 495 | 1 | 0.0173758378195 |
| step | bbox_err | 918 | 0.166666984843 | 0.172891961817 | 0 | 375 | 400 | 143 | 0.388642682322 |
| point | cd | 717 | 51.3260508759 | 12.6550248072 | -33.2195991776 | 632 | 85 | 0 | 3.48024101431e-104 |
| point | f_score_1pct | 717 | 0.0209847383721 | 0.0546177455357 | 0.0188939267113 | 494 | 206 | 17 | 3.48811047978e-28 |
| point | bbox_err | 717 | 17.4066667553 | 6.50637164434 | -8.88605128204 | 643 | 74 | 0 | 4.06733298342e-114 |
| text | cd | 731 | 3.9020401946 | 3.97855227127 | -0.0506115347806 | 425 | 306 | 0 | 1.22296715922e-05 |
| text | f_score_1pct | 731 | 0.161607817221 | 0.167963072311 | 0.00444835694482 | 398 | 331 | 2 | 0.0144515707576 |
| text | bbox_err | 731 | 0.203333139403 | 0.333333015905 | 0 | 324 | 309 | 98 | 0.577937916526 |
| image | cd | 750 | 53.2327160559 | 12.2184882966 | -28.9213350655 | 639 | 111 | 0 | 5.94018341581e-91 |
| image | f_score_1pct | 750 | 0.0265713778409 | 0.0560380636284 | 0.0133582432628 | 490 | 245 | 15 | 1.03562373865e-19 |
| image | bbox_err | 750 | 17.5252128143 | 6.67729691814 | -8.513335903 | 649 | 101 | 0 | 8.79386344177e-99 |

## All Metric Distributions

Sample SD describes variation between scored cases, not training-run uncertainty. Quantiles use linear interpolation at(n-1)*p. F@1 values here are fractions.

| Modality | Arm | Set/metric | N | Mean | Median | Sample SD | Min | Q25 | Q75 | Q95 | Q99 | Max |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| step | A | conditional/cd | 1463 | 17.7998429033 | 3.14271984606 | 96.541344191 | 0.0276895543141 | 1.8936230748 | 8.47573703881 | 48.3652788227 | 293.910040098 | 2264.23016538 |
| step | A | conditional/f_score_1pct | 1463 | 0.18447094037 | 0.187976866883 | 0.101034877782 | 0 | 0.0964293754486 | 0.25664405774 | 0.351070279903 | 0.399085005596 | 0.474609375 |
| step | A | conditional/bbox_err | 1463 | 2.41126480147 | 0.295178566872 | 5.60863702659 | 0 | 0.00405768238678 | 1.40830921495 | 12.4911688235 | 27.8177339174 | 53.6600054214 |
| step | A | conditional/target_bbox_diag | 1463 | 78.4040950278 | 83.5014417691 | 23.9938597421 | 9.39466310481 | 68.4836231518 | 95.1221526686 | 108.621834578 | 117.95610798 | 126.560143188 |
| step | A | conditional/gen_bbox_diag | 1463 | 77.6815380016 | 82.4810749698 | 27.0882803526 | 5.06310278955 | 65.8244163034 | 95.7236553553 | 113.123438725 | 138.161487802 | 155.621085691 |
| step | A | conditional/bbox_ratio_to_gt | 1463 | 0.985138308639 | 1 | 0.124773100685 | 0.0545092039663 | 0.997662974628 | 1.00349445096 | 1.09558460239 | 1.42945316552 | 1.53970674915 |
| step | A | unconditional/f_score_1pct | 2500 | 0.107952394305 | 0.0634765625 | 0.11931353718 | 0 | 0 | 0.20702779518 | 0.324715783026 | 0.386711370504 | 0.474609375 |
| step | A | paired/cd | 918 | 17.4652136924 | 3.14417336119 | 78.1724325302 | 0.0276895543141 | 1.82883746064 | 7.32931114262 | 55.2240822606 | 377.169993269 | 1131.24448292 |
| step | A | paired/f_score_1pct | 918 | 0.169124732374 | 0.166501034007 | 0.0919415685185 | 0 | 0.0878824869792 | 0.233511068965 | 0.32419923025 | 0.385381249031 | 0.428702039436 |
| step | A | paired/bbox_err | 918 | 2.13138752724 | 0.166666984843 | 5.6835422259 | 0 | 0.000489720813558 | 0.83333313508 | 13.5909783286 | 28.3280673284 | 46.8233469741 |
| step | B | conditional/cd | 1325 | 115820333.023 | 3.59055349289 | 4215922994.54 | 0.0269149095191 | 1.75194199917 | 8.36293084154 | 110.177175646 | 342.509126853 | 153461913446 |
| step | B | conditional/f_score_1pct | 1325 | 0.151226821582 | 0.145004734848 | 0.0818093760144 | 0 | 0.0831505847953 | 0.207989473298 | 0.293412021631 | 0.35181572857 | 0.4257610916 |
| step | B | conditional/bbox_err | 1325 | 253.904000988 | 0.299999952298 | 9157.39677979 | 0 | 0.00872006245593 | 0.933334032667 | 16.4485479585 | 31.9813331607 | 333336.533333 |
| step | B | conditional/target_bbox_diag | 1325 | 75.1257266095 | 81.7579858632 | 26.2135081633 | 9.39466310481 | 60.5593008497 | 94.1132308411 | 108.982728053 | 119.470596815 | 126.560143188 |
| step | B | conditional/gen_bbox_diag | 1325 | 828.298640795 | 80.3006608348 | 27470.5981283 | 9.3905121121 | 53.5425156795 | 93.4386703357 | 109.394908082 | 123.958170831 | 1000018.00487 |
| step | B | conditional/bbox_ratio_to_gt | 1325 | 8.69510910853 | 0.999999999991 | 280.602765769 | 0.208094378373 | 0.995947159495 | 1.00198005305 | 1.09592679183 | 1.31201684023 | 10215.0800607 |
| step | B | unconditional/f_score_1pct | 2500 | 0.0801502154386 | 0.0334133993271 | 0.0961509043435 | 0 | 0 | 0.151844478497 | 0.264180830046 | 0.330062118706 | 0.4257610916 |
| step | B | paired/cd | 918 | 167169856.418 | 3.75183308486 | 5064997884.1 | 0.0269149095191 | 1.95630337933 | 7.95124908782 | 87.8468908391 | 243.260300765 | 153461913446 |
| step | B | paired/f_score_1pct | 918 | 0.162677827581 | 0.163074242141 | 0.0823960321518 | 0 | 0.097646484375 | 0.218681335449 | 0.299495347192 | 0.351884088077 | 0.4257610916 |
| step | B | paired/bbox_err | 918 | 365.036298126 | 0.172891961817 | 11001.6826216 | 0 | 0.00333408541398 | 0.766667381972 | 11.1049293972 | 28.7693333883 | 333336.533333 |
| point | A | conditional/cd | 1267 | 88.0688650759 | 56.2136549593 | 110.998902578 | 0.0880384287072 | 23.2381672196 | 118.174553417 | 262.092851129 | 466.58966342 | 1838.25665028 |
| point | A | conditional/f_score_1pct | 1267 | 0.0469744110434 | 0.0351291232639 | 0.0443273956091 | 0 | 0.00941676493711 | 0.0736433688047 | 0.125640443314 | 0.179432921287 | 0.277789982425 |
| point | A | conditional/bbox_err | 1267 | 19.1398464734 | 18.0512975278 | 10.5789236759 | 0.225528545517 | 11.2333335399 | 26.0199997158 | 35.604461046 | 45.2260908644 | 105.000002098 |
| point | A | conditional/target_bbox_diag | 1267 | 81.7448609149 | 84.9902055522 | 21.5611435999 | 9.39466310481 | 73.0600616429 | 95.7104353711 | 108.604177748 | 119.74916564 | 127.136622995 |
| point | A | conditional/gen_bbox_diag | 1267 | 58.718572971 | 52.4236587811 | 35.7820775527 | 6.62099423346 | 31.8254615049 | 71.9333315722 | 142.612013734 | 181.8420797 | 294.16774648 |
| point | A | conditional/bbox_ratio_to_gt | 1267 | 0.748247462469 | 0.672603959932 | 0.430143477868 | 0.0633957636837 | 0.4474201169 | 0.92388085786 | 1.51971174152 | 2.26152408671 | 4.57723500213 |
| point | A | unconditional/f_score_1pct | 2500 | 0.0238066315168 | 0 | 0.0393344651199 | 0 | 0 | 0.0365625 | 0.107637181897 | 0.162175637858 | 0.277789982425 |
| point | A | paired/cd | 717 | 84.5215345693 | 51.3260508759 | 99.5772072431 | 0.0880384287072 | 23.1520846134 | 108.315485321 | 275.696298834 | 500.166384254 | 754.388311674 |
| point | A | paired/f_score_1pct | 717 | 0.0357696662459 | 0.0209847383721 | 0.0395404824643 | 0 | 0.0068359375 | 0.0539836711712 | 0.112549779698 | 0.165775278804 | 0.277789982425 |
| point | A | paired/bbox_err | 717 | 18.0829005348 | 17.4066667553 | 10.0871492478 | 0.225528545517 | 10.8233340581 | 24.4066683451 | 35.1787966602 | 46.1277342545 | 64.4750008585 |
| point | B | conditional/cd | 1188 | 24.4356077902 | 11.2261716224 | 40.6793804488 | 0.0696044712892 | 4.33982884441 | 26.1867020205 | 96.4911310513 | 180.403279812 | 524.719438781 |
| point | B | conditional/f_score_1pct | 1188 | 0.0629509361004 | 0.0526891637731 | 0.053423640889 | 0 | 0.0170863560268 | 0.0965835406669 | 0.163827553596 | 0.206462708939 | 0.30949329653 |
| point | B | conditional/bbox_err | 1188 | 7.89351011866 | 5.82833318108 | 6.8211113624 | 0.0743363445026 | 2.7333342077 | 10.6691675782 | 22.4863175123 | 31.2219354894 | 40.9106635 |
| point | B | conditional/target_bbox_diag | 1188 | 75.2763747518 | 81.8863231901 | 26.7953812941 | 9.39466310481 | 58.8834819689 | 95.2045935051 | 109.327045029 | 119.606439658 | 126.560143188 |
| point | B | conditional/gen_bbox_diag | 1188 | 65.3278035285 | 71.6458231292 | 25.2660209225 | 8.49000202497 | 41.4543893521 | 84.6720150747 | 103.658575802 | 109.66600502 | 116.474385758 |
| point | B | conditional/bbox_ratio_to_gt | 1188 | 0.891469595202 | 0.906530028621 | 0.212676295857 | 0.202140657912 | 0.795116262229 | 1.00490865871 | 1.17947918984 | 1.39574632288 | 2.15858791867 |
| point | B | unconditional/f_score_1pct | 2500 | 0.0299142848349 | 0 | 0.0484182328958 | 0 | 0 | 0.0482954545455 | 0.136027105735 | 0.190708985813 | 0.30949329653 |
| point | B | paired/cd | 717 | 25.4740703967 | 12.6550248072 | 40.3340323528 | 0.0696044712892 | 5.91656275138 | 27.1033991995 | 96.1767838757 | 165.14394963 | 524.719438781 |
| point | B | paired/f_score_1pct | 717 | 0.0653361826567 | 0.0546177455357 | 0.0572769716632 | 0 | 0.015625 | 0.102455357143 | 0.175742849777 | 0.246064126116 | 0.30949329653 |
| point | B | paired/bbox_err | 717 | 8.27439663428 | 6.50637164434 | 6.22273167366 | 0.0743363445026 | 3.59333356245 | 11.3033338391 | 20.081135469 | 27.8353809311 | 40.9106635 |
| text | A | conditional/cd | 1233 | 262235222.222 | 4.39517460505 | 6509814421.39 | 0.027245839004 | 2.21065356712 | 17.6962592255 | 91.0209689568 | 281.097615427 | 164909271717 |
| text | A | conditional/f_score_1pct | 1233 | 0.159389689461 | 0.160132431402 | 0.100056983193 | 0 | 0.0702582465278 | 0.226545662716 | 0.328296805349 | 0.384510735504 | 0.524898255814 |
| text | A | conditional/bbox_err | 1233 | 595.147963483 | 0.371886127261 | 14747.5512033 | 0 | 0.0366674665091 | 2.59165687474 | 17.0091196659 | 36.8860863702 | 396573.805058 |
| text | A | conditional/target_bbox_diag | 1233 | 78.4872888473 | 83.7184587504 | 24.2130679094 | 9.39466310481 | 68.8279497717 | 95.2386005437 | 108.371744361 | 119.572989883 | 126.560143188 |
| text | A | conditional/gen_bbox_diag | 1233 | 1699.06203006 | 82.9800890924 | 40255.282965 | 5.0834120375 | 64.7182220543 | 95.7927254169 | 113.881749226 | 130.635414787 | 1000000.00144 |
| text | A | conditional/bbox_ratio_to_gt | 1233 | 35.4280945049 | 0.999999999991 | 854.85082473 | 0.0559921093197 | 0.991871066396 | 1.00311749488 | 1.1573612596 | 1.57175835475 | 21423.5182219 |
| text | A | unconditional/f_score_1pct | 2500 | 0.078610994842 | 0 | 0.106246066752 | 0 | 0 | 0.158409820744 | 0.290034994111 | 0.360290937562 | 0.524898255814 |
| text | A | paired/cd | 731 | 17.0760138847 | 3.9020401946 | 48.0223233433 | 0.027245839004 | 2.02870150337 | 11.9669360444 | 68.5513318375 | 200.552672307 | 636.583664778 |
| text | A | paired/f_score_1pct | 731 | 0.161806372848 | 0.161607817221 | 0.0959050999516 | 0 | 0.0793322229678 | 0.228489594985 | 0.320723533701 | 0.377081699286 | 0.524898255814 |
| text | A | paired/bbox_err | 731 | 2.17536534708 | 0.203333139403 | 5.51323084761 | 0 | 0.0189019410455 | 1.53388440367 | 10.5258341474 | 32.9100069047 | 44.993403967 |
| text | B | conditional/cd | 1192 | 399716301.791 | 3.91862330554 | 7964297535.62 | 0.0269040654613 | 2.02664099266 | 9.64335001989 | 120.766026595 | 422.701922208 | 164158035120 |
| text | B | conditional/f_score_1pct | 1192 | 0.156543657659 | 0.15592267745 | 0.082269285967 | 0 | 0.091127064084 | 0.213978961808 | 0.29672879626 | 0.365929783548 | 0.523870718779 |
| text | B | conditional/bbox_err | 1192 | 841.6949572 | 0.33333333352 | 16708.7336561 | 0 | 0.0130851428889 | 1.39000283539 | 18.8190687103 | 31.7375458123 | 333349.240001 |
| text | B | conditional/target_bbox_diag | 1192 | 77.3630304753 | 83.5614487309 | 25.3785222995 | 9.39466310481 | 66.8253574625 | 94.8810813914 | 109.202129769 | 119.600920478 | 126.560143188 |
| text | B | conditional/gen_bbox_diag | 1192 | 2591.81893036 | 80.6851281329 | 50122.5033831 | 9.38775432302 | 59.4811441396 | 94.0861780855 | 112.048749144 | 125.43895636 | 1000026.04331 |
| text | B | conditional/bbox_ratio_to_gt | 1192 | 38.2904930986 | 0.999746485355 | 795.008277465 | 0.183462331386 | 0.991462057231 | 1.00035118297 | 1.06817041969 | 1.38864764938 | 22777.5377182 |
| text | B | unconditional/f_score_1pct | 2500 | 0.074640015972 | 0 | 0.0966509857163 | 0 | 0 | 0.150333553166 | 0.256848994878 | 0.329596808838 | 0.523870718779 |
| text | B | paired/cd | 731 | 224566418.918 | 3.97855227127 | 6071604255.13 | 0.0269040654613 | 2.0027420697 | 9.28674276718 | 68.2673754302 | 410.090933993 | 164158035120 |
| text | B | paired/f_score_1pct | 731 | 0.166260292331 | 0.167963072311 | 0.0832127656533 | 0.00130208333333 | 0.0992017939885 | 0.221800948226 | 0.308104694929 | 0.377445719624 | 0.523870718779 |
| text | B | paired/bbox_err | 731 | 458.353707097 | 0.333333015905 | 12328.8462721 | 0 | 0.0162609491127 | 1.22365140994 | 15.1366092015 | 30.3951013956 | 333337.466668 |
| image | A | conditional/cd | 1283 | 122054510.044 | 60.3670399429 | 4371866050.21 | 0.104375654719 | 26.6609755079 | 117.188036523 | 270.236851846 | 425.96143795 | 156595823699 |
| image | A | conditional/f_score_1pct | 1283 | 0.0510134225894 | 0.0406436011905 | 0.04556307437 | 0 | 0.0136021205357 | 0.0803084415584 | 0.134678770925 | 0.196900640544 | 0.258093100189 |
| image | A | conditional/bbox_err | 1283 | 279.02518269 | 18.6066649753 | 9305.45857931 | 0.19219540285 | 12.1147396352 | 25.8764805997 | 36.6315561324 | 45.3768682315 | 333331.157629 |
| image | A | conditional/target_bbox_diag | 1283 | 81.8098671539 | 85.7399954503 | 22.3390305456 | 9.39466310481 | 73.4506382602 | 95.9466280094 | 109.083881496 | 117.810353252 | 126.560143188 |
| image | A | conditional/gen_bbox_diag | 1283 | 835.182376305 | 51.6320742491 | 27916.6687529 | 5.96376177695 | 30.2997441229 | 71.2061762712 | 114.781660248 | 178.463550366 | 1000002.00108 |
| image | A | conditional/bbox_ratio_to_gt | 1283 | 18.7163374403 | 0.660224248051 | 644.674714026 | 0.07184965757 | 0.429401186239 | 0.906608459269 | 1.36199310706 | 2.41562637731 | 23092.3104425 |
| image | A | unconditional/f_score_1pct | 2500 | 0.0261800884729 | 0 | 0.0414173228864 | 0 | 0 | 0.0428869226477 | 0.114616339088 | 0.166526678762 | 0.258093100189 |
| image | A | paired/cd | 750 | 208794509.428 | 53.2327160559 | 5718071000.55 | 0.104375654719 | 22.0308558178 | 100.62675549 | 254.343429875 | 437.846274522 | 156595823699 |
| image | A | paired/f_score_1pct | 750 | 0.042213083121 | 0.0265713778409 | 0.0438466534484 | 0 | 0.00885331003289 | 0.0629722963719 | 0.124041191126 | 0.196133533842 | 0.258093100189 |
| image | A | paired/bbox_err | 750 | 462.096861006 | 17.5252128143 | 12170.8915408 | 0.19219540285 | 10.5499989984 | 23.6844229405 | 35.4066669783 | 44.8523948058 | 333331.157629 |
| image | B | conditional/cd | 1264 | 45.7648842896 | 8.39662810118 | 163.811724579 | 0.0833619632473 | 3.0275490926 | 22.1749824225 | 137.643815269 | 1080.32591556 | 1389.33305053 |
| image | B | conditional/f_score_1pct | 1264 | 0.0607139021886 | 0.050771859976 | 0.0510447596464 | 0 | 0.0180268158784 | 0.0893367913251 | 0.159748099757 | 0.21134779157 | 0.283320580971 |
| image | B | conditional/bbox_err | 1264 | 7.30907978097 | 4.87333301553 | 6.95939399537 | 0.0100002297061 | 2.32166672779 | 9.86666623731 | 22.9131751439 | 31.4783533415 | 41.1293320492 |
| image | B | conditional/target_bbox_diag | 1264 | 71.0304823266 | 77.791679486 | 27.6853979943 | 9.39466310481 | 44.2115000934 | 93.1041031782 | 108.909652881 | 119.751167155 | 125.578223443 |
| image | B | conditional/gen_bbox_diag | 1264 | 63.9736228685 | 66.2080154437 | 27.3740325234 | 7.29409820362 | 39.4862721199 | 85.2503710416 | 107.295163618 | 115.10511388 | 149.763870075 |
| image | B | conditional/bbox_ratio_to_gt | 1264 | 0.919790468074 | 0.92865804329 | 0.217399342729 | 0.0710115131778 | 0.83265570848 | 1.01953988166 | 1.1984451548 | 1.49433547283 | 2.36547386778 |
| image | B | unconditional/f_score_1pct | 2500 | 0.0306969489466 | 0 | 0.0473144485187 | 0 | 0 | 0.0514952461675 | 0.132854150139 | 0.193938263628 | 0.283320580971 |
| image | B | paired/cd | 750 | 58.5593165713 | 12.2184882966 | 197.603480455 | 0.0833619632473 | 5.42775257718 | 27.0325098995 | 138.642734292 | 1172.69167771 | 1389.33305053 |
| image | B | paired/f_score_1pct | 750 | 0.065594722611 | 0.0560380636284 | 0.0557555579967 | 0 | 0.0159801136364 | 0.102522786458 | 0.172012486287 | 0.216264226919 | 0.283320580971 |
| image | B | paired/bbox_err | 750 | 8.44336734613 | 6.67729691814 | 6.96269207937 | 0.0100002297061 | 3.29021082029 | 11.399999334 | 22.7505975347 | 31.675934259 | 41.1293320492 |

## Paired Gate Tables

| Modality | Flag | Both pass | A only | B only | Both fail | Exact McNemar p |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| step | build_ok | 1036 | 488 | 411 | 565 | 0.0112120438893 |
| step | exec_ok | 1036 | 488 | 411 | 565 | 0.0112120438893 |
| step | solid_valid | 1036 | 488 | 411 | 565 | 0.0112120438893 |
| step | step_export_ok | 977 | 525 | 407 | 591 | 0.000124455394484 |
| step | syntax_ok | 2042 | 390 | 45 | 23 | 1.08685507623e-69 |
| point | build_ok | 876 | 439 | 482 | 703 | 0.166339595629 |
| point | exec_ok | 876 | 439 | 482 | 703 | 0.166339595629 |
| point | solid_valid | 876 | 439 | 482 | 703 | 0.166339595629 |
| point | step_export_ok | 779 | 515 | 477 | 729 | 0.240079312848 |
| point | syntax_ok | 2018 | 418 | 46 | 18 | 3.89639512037e-76 |
| text | build_ok | 846 | 415 | 502 | 737 | 0.00448597166139 |
| text | exec_ok | 846 | 415 | 502 | 737 | 0.00448597166139 |
| text | solid_valid | 846 | 415 | 502 | 737 | 0.00448597166139 |
| text | step_export_ok | 811 | 434 | 484 | 771 | 0.105775093883 |
| text | syntax_ok | 2087 | 372 | 37 | 4 | 9.79004163302e-71 |
| image | build_ok | 888 | 464 | 533 | 615 | 0.0312215599262 |
| image | exec_ok | 888 | 464 | 533 | 615 | 0.0312215599262 |
| image | solid_valid | 888 | 464 | 533 | 615 | 0.0312215599262 |
| image | step_export_ok | 819 | 502 | 518 | 661 | 0.638613487644 |
| image | syntax_ok | 2047 | 379 | 72 | 2 | 2.17902753649e-51 |

## Failure Inventories And Native Run Metadata

Every exact native error string/count follows. All failure IDs, scored IDs, export-but-unscoreable IDs, zero/one-F@1 IDs, extreme-CD cases and every raw gate/geometry record are retained in the summary/per-case JSON files; no case is omitted. Native error text is an evaluator outcome, not an independently validated causal taxonomy.

### step / A

Scoreable=1463; target-present=2500; missing-target=0; kernel-crashes=0; export-but-unscoreable=39; gate/geometry flag-mismatch cases=0; CD>1000 scored cases=4.
First failure stages: `{"exec_ok_failure": 908, "post_export_geometry_failure": 39, "scoreable": 1463, "step_export_ok_failure": 22, "syntax_ok_failure": 68}`.
Geometry-run gate counts: `{"build_ok": 1524, "exec_ok": 1524, "solid_valid": 1524, "step_export_ok": 1502, "syntax_ok": 2432}`.
Native gate runtime seconds=424.516; native geometry Python=3.11.11. Geometry runtime is not separately measured by this script; no wall-time estimate is invented.
Retained last-attempt geometry resume messages: `[]`. The last log is not a complete independent retry history.

| Count | Exact error |
| ---: | --- |
| 148 | exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face |
| 83 | exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float' |
| 39 | point cloud sampling failed on generated part |
| 33 | exec error: Part.circular_pattern() got an unexpected keyword argument 'radius' |
| 33 | exec error: 'Part' object has no attribute 'loft_on_face' |
| 32 | exec error: 'Part' object has no attribute 'profile_set' |
| 30 | exec error: mirror: plane must be 'YZ', 'XZ', or 'XY' |
| 27 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path_offset_y' |
| 26 | SyntaxError: invalid syntax (<unknown>, line 1) |
| 24 | exec error: extrude_on_face join/add requires height |
| 24 | exec error: target must be a TopologyReference from a FeatureHandle |
| 23 | exec error: 'Part' object has no attribute 'profile_plain' |
| 22 | STEP export error: OCCT build failed |
| 17 | exec error: Part.cylinder() got an unexpected keyword argument 'length' |
| 17 | exec error: topology reference 'revolve_001:top_face:d95ca6795e31' did not resolve any face |
| 16 | exec error: 'Part' object has no attribute 'electronics_enclosure' |
| 15 | exec error: Part.plate() got an unexpected keyword argument 'length' |
| 15 | exec error: unsupported operand type(s) for /: 'ParameterRef' and 'float' |
| 12 | exec error: Part.extrude() got an unexpected keyword argument 'operation' |
| 12 | exec error: 'FeatureHandle' object has no attribute 'pocket_boundary' |
| 12 | SyntaxError: unmatched ']' (<unknown>, line 1) |
| 11 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path_width' |
| 11 | exec error: parameter 'path_length' already exists |
| 10 | exec error: Part.cone() got an unexpected keyword argument 'height_over_radius' |
| 10 | exec error: Part.sweep_tube() got an unexpected keyword argument 'profile_points' |
| 10 | exec error: Part.torus() got an unexpected keyword argument 'radius_outer' |
| 10 | exec error: Part.standoff_array_plate() got an unexpected keyword argument 'height_direction' |
| 10 | exec error: Part.rotate() got an unexpected keyword argument 'angle' |
| 9 | exec error: Part.standoff_array_plate() got an unexpected keyword argument 'hole_positions' |
| 9 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path' |
| 8 | exec error: Part.boolean_cut() got an unexpected keyword argument 'offset' |
| 8 | exec error: 'Part' object has no attribute 'sweep_flange' |
| 7 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'profile' |
| 7 | exec error: 'Part' object has no attribute 'offset_hole_pattern' |
| 6 | exec error: 'Part' object has no attribute 'crescent_lug_profile' |
| 6 | exec error: 'Part' object has no attribute 'counterbore_positioned_decoration' |
| 6 | exec error: 'Part' object has no attribute 'sweep_profile' |
| 6 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_from' |
| 5 | exec error: Part.hole_pattern() got an unexpected keyword argument 'offset' |
| 5 | exec error: 'Part' object has no attribute 'sweep_annular_path' |
| 5 | SyntaxError: invalid syntax (<unknown>, line 2) |
| 5 | exec error: 'Part' object has no attribute 'hole_on_face' |
| 5 | exec error: Part.sweep_tube() got an unexpected keyword argument 'profile_length' |
| 4 | exec error: 'Part' object has no attribute 'box_on_face' |
| 4 | exec error: Part.box() got an unexpected keyword argument 'thickness' |
| 4 | exec error: 'Part' object has no attribute 'boolean_add' |
| 4 | SyntaxError: unterminated string literal (detected at line 9) (<unknown>, line 9) |
| 4 | exec error: hole depth must be a number or 'through' |
| 4 | exec error: 'Part' object has no attribute 'face_add_on_face' |
| 4 | exec error: row_step must be a 3D sequence |
| 4 | exec error: topology reference 'join_002:top_face:323af5d41048' did not resolve any face |
| 3 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'semantic_profile' |
| 3 | exec error: 'upper_length' |
| 3 | exec error: 'Part' object has no attribute 'face_mask' |
| 3 | SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 1) |
| 3 | exec error: 'boss_radius' |
| 3 | exec error: 'list' object has no attribute 'strip' |
| 3 | exec error: Part.boolean_join() got an unexpected keyword argument 'operation' |
| 3 | exec error: target must be a FeatureHandle |
| 3 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_reference' |
| 3 | exec error: Part.sweep_tube() got an unexpected keyword argument 'thickness' |
| 3 | exec error: topology reference 'hole_001:top_face:9014e73e3f7b' did not resolve any face |
| 3 | exec error: 'Part' object has no attribute 'rectangular_slot' |
| 3 | SyntaxError: invalid syntax (<unknown>, line 25) |
| 3 | exec error: 'cut_height' |
| 2 | exec error: parameter 'boss_height' already exists |
| 2 | exec error: 'FeatureHandle' object has no attribute 'profile' |
| 2 | exec error: Part.bossed_plate() got an unexpected keyword argument 'profile_segments' |
| 2 | exec error: Part.box() got an unexpected keyword argument 'target' |
| 2 | exec error: 'Part' object has no attribute 'extrude_on_sketch' |
| 2 | exec error: 'width' |
| 2 | exec error: Part.sweep_tube() got an unexpected keyword argument 'profile_height' |
| 2 | exec error: extrude_on_face cut requires depth |
| 2 | exec error: Part.sweep_tube() got an unexpected keyword argument 'profile_width' |
| 2 | exec error: 'Part' object has no attribute 'boolean_boolean' |
| 2 | exec error: 'Part' object has no attribute 'face_add_on_profile' |
| 2 | exec error: parameter 'fillet_radius' already exists |
| 2 | exec error: 'Part' object has no attribute 'rectangular_cut' |
| 2 | exec error: 'Part' object has no attribute 'face_on_top' |
| 2 | exec error: Part.bossed_plate() got an unexpected keyword argument 'profile_radius' |
| 2 | exec error: 'Part' object has no attribute 'top_face' |
| 2 | exec error: Part.shell() got an unexpected keyword argument 'sides' |
| 2 | exec error: name 'fillet_edges' is not defined |
| 2 | exec error: 'Part' object has no attribute 'loft_on_edges' |
| 2 | SyntaxError: unterminated string literal (detected at line 18) (<unknown>, line 18) |
| 2 | exec error: 'Part' object has no attribute 'profile_cut' |
| 2 | exec error: Part.sweep_tube() missing 2 required keyword-only arguments: 'radius' and 'path_mid_length' |
| 2 | exec error: 'Part' object has no attribute 'face' |
| 2 | exec error: 'Part' object has no attribute 'counterbore_hole_pattern' |
| 2 | exec error: 'Part' object has no attribute 'face_cut_on_face' |
| 2 | exec error: 'Part' object has no attribute 'revolve_on_face' |
| 2 | exec error: 'height' |
| 2 | exec error: 'Part' object has no attribute 'loft_on_plane' |
| 2 | exec error: Part.hole_pattern() got an unexpected keyword argument 'profile' |
| 2 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'thread_segments' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path_length_2' |
| 1 | exec error: 'Part' object has no attribute 'counterbore_position' |
| 1 | exec error: 'Part' object has no attribute 'tube' |
| 1 | SyntaxError: invalid syntax. Maybe you meant '==' or ':=' instead of '='? (<unknown>, line 1) |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 7) |
| 1 | exec error: 'cut_width' |
| 1 | exec error: 'Part' object has no attribute 'foot' |
| 1 | exec error: topology reference 'cut_002:top_face:d7e817b6f02b' did not resolve any face |
| 1 | exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'offset_hole_row' |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'diameter' |
| 1 | exec error: 'through_bolt_length' |
| 1 | exec error: 'Part' object has no attribute 'bosses' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 19) |
| 1 | exec error: 'Part' object has no attribute 'boolean_filter' |
| 1 | SyntaxError: unterminated string literal (detected at line 40) (<unknown>, line 40) |
| 1 | exec error: 'Part' object has no attribute 'profile_rectangle' |
| 1 | exec error: points[] must be a 2D sequence |
| 1 | exec error: Part.sketch_rectangle() got an unexpected keyword argument 'semantic_profile_id' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 39) |
| 1 | exec error: 'Part' object has no attribute 'loft_on_x_axis' |
| 1 | exec error: 'Part' object has no attribute 'profile_half_profile' |
| 1 | exec error: 'Part' object has no attribute 'electronics_enclosure_plate' |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_guides' |
| 1 | exec error: bad operand type for unary -: 'ParameterRef' |
| 1 | exec error: 'lower_width' |
| 1 | exec error: 'Part' object has no attribute 'loft_on_rect_profile' |
| 1 | exec error: 'upper_plate_width' |
| 1 | exec error: 'Part' object has no attribute 'lofted_flange' |
| 1 | exec error: keyword argument repeated: width (<candidate>, line 10) |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path_offset_x' |
| 1 | exec error: 'upper_height' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'nearest_edges' |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'flange_radius' |
| 1 | exec error: Part.standoff_array_plate() got an unexpected keyword argument 'hole_spacing' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 10) |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 20) |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 10) |
| 1 | exec error: 'Part' object has no attribute 'loft_profile' |
| 1 | exec error: 'hole_profile' |
| 1 | exec error: 'Part' object has no attribute 'facedadity' |
| 1 | exec error: Part.standoff_array_plate() got an unexpected keyword argument 'standoff_count' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'pipe_radius' |
| 1 | exec error: 'Part' object has no attribute 'footprint' |
| 1 | exec error: Part.hole_pattern() got an unexpected keyword argument 'offsets' |
| 1 | exec error: Part.sweep_tube() missing 1 required keyword-only argument: 'path_mid_length' |
| 1 | exec error: name 'fillet_radius' is not defined |
| 1 | exec error: topology reference 'loft_001:top_face:b95a905e855a' did not resolve any face |
| 1 | exec error: 'Part' object has no attribute 'plate_enclosure' |
| 1 | exec error: 'flange_length' |
| 1 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'width' |
| 1 | no `part` variable after execution |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 9) |
| 1 | exec error: Part.translate() got an unexpected keyword argument 'reference' |
| 1 | exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'tool' |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'radius' |
| 1 | exec error: 'Part' object has no attribute 'rectangular_rib' |
| 1 | SyntaxError: invalid syntax. Maybe you meant '==' or ':=' instead of '='? (<unknown>, line 25) |
| 1 | exec error: 'Part' object has no attribute 'lofted_transition' |
| 1 | SyntaxError: unterminated string literal (detected at line 16) (<unknown>, line 16) |
| 1 | exec error: keyword argument repeated: radius (<candidate>, line 20) |
| 1 | exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'distance' |
| 1 | exec error: name 'profile_rectangle' is not defined |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 38) |
| 1 | exec error: topology reference 'cut_001:top_face:e6c86e3e481d' did not resolve any face |
| 1 | exec error: 'Part' object has no attribute 'pin' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'profile' |
| 1 | SyntaxError: cannot assign to attribute here. Maybe you meant '==' instead of '='? (<unknown>, line 1) |
| 1 | exec error: 'Part' object has no attribute 'lofted_transition_between_plates' |
| 1 | exec error: Part.boolean_cut() got an unexpected keyword argument 'depth' |
| 1 | exec error: 'upper_width' |
| 1 | exec error: Part.cone() got an unexpected keyword argument 'height_top' |
| 1 | exec error: 'Part' object has no attribute 'counterbore_slot_on_face' |
| 1 | exec error: 'Part' object has no attribute 'flange_on_face' |
| 1 | exec error: 'Part' object has no attribute 'boolean_select' |

### step / B

Scoreable=1325; target-present=2500; missing-target=0; kernel-crashes=0; export-but-unscoreable=59; gate/geometry flag-mismatch cases=0; CD>1000 scored cases=1.
First failure stages: `{"exec_ok_failure": 640, "post_export_geometry_failure": 59, "scoreable": 1325, "step_export_ok_failure": 63, "syntax_ok_failure": 413}`.
Geometry-run gate counts: `{"build_ok": 1447, "exec_ok": 1447, "solid_valid": 1447, "step_export_ok": 1384, "syntax_ok": 2087}`.
Native gate runtime seconds=851.186; native geometry Python=3.11.11. Geometry runtime is not separately measured by this script; no wall-time estimate is invented.
Retained last-attempt geometry resume messages: `[]`. The last log is not a complete independent retry history.

| Count | Exact error |
| ---: | --- |
| 354 | SyntaxError: unmatched ']' (<unknown>, line 1) |
| 63 | STEP export error: OCCT build failed |
| 61 | exec error: topology reference 'revolve_001:top_face:d95ca6795e31' did not resolve any face |
| 59 | point cloud sampling failed on generated part |
| 53 | exec error: Part.plate() got an unexpected keyword argument 'length' |
| 51 | exec error: points[] must be a 2D sequence |
| 41 | exec error: Part.circular_pattern() got an unexpected keyword argument 'radius' |
| 27 | exec error: topology reference 'join_002:top_face:323af5d41048' did not resolve any face |
| 25 | exec error: Part.sketch_on_face() got an unexpected keyword argument 'face' |
| 20 | exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float' |
| 16 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'profile' |
| 14 | exec error: Part.revolve() got an unexpected keyword argument 'thickness' |
| 14 | SyntaxError: invalid syntax (<unknown>, line 1) |
| 13 | exec error: 'Part' object has no attribute 'lofted_loop' |
| 13 | exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face |
| 12 | exec error: mirror: plane must be 'YZ', 'XZ', or 'XY' |
| 11 | exec error: target must be a FeatureHandle |
| 10 | exec error: target must be a TopologyReference from a FeatureHandle |
| 10 | exec error: extrude_on_face cut requires depth |
| 9 | exec error: Part.sketch_on_face() got an unexpected keyword argument 'closed' |
| 9 | exec error: Part.loft() got an unexpected keyword argument 'target' |
| 8 | exec error: Part.wedge() got an unexpected keyword argument 'width' |
| 8 | exec error: 'Part' object has no attribute 'callout_on_face' |
| 8 | exec error: 'lower_radius' |
| 7 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'height' |
| 7 | exec error: 'Part' object has no attribute 'move' |
| 7 | exec error: bad operand type for unary -: 'ParameterRef' |
| 6 | exec error: Part.boolean_cut() got an unexpected keyword argument 'depth' |
| 6 | exec error: 'Part' object has no attribute 'rectangular_pocket_profile' |
| 6 | exec error: topology reference 'pocket_001:top_outer_edges:0501fba53d98' did not resolve any edge_set |
| 6 | exec error: Part.hole_pattern() got an unexpected keyword argument 'position' |
| 5 | SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 1) |
| 5 | exec error: 'Part' object has no attribute 'box_on_face' |
| 5 | exec error: topology reference 'pocket_001:top_face:6bc5ae6c80c5' did not resolve any face |
| 5 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 10) |
| 5 | exec error: 'Part' object has no attribute 'rectangular_cut' |
| 5 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_reference' |
| 4 | exec error: Part.hole_pattern() got an unexpected keyword argument 'offsets' |
| 4 | exec error: 'Part' object has no attribute 'boolean_solid_join' |
| 4 | exec error: topology reference 'loft_001:top_face:b95a905e855a' did not resolve any face |
| 4 | exec error: Part.extrude() got an unexpected keyword argument 'thickness' |
| 4 | exec error: extrude_on_face join/add requires height |
| 4 | exec error: Part.cylinder() got an unexpected keyword argument 'target' |
| 4 | exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'jaw_spacing' |
| 4 | exec error: 'Part' object has no attribute 'extrude_profile' |
| 3 | exec error: topology reference 'cut_001:top_face:e6c86e3e481d' did not resolve any face |
| 3 | exec error: 'FeatureHandle' object has no attribute 'min_corner' |
| 3 | exec error: topology reference 'extrude_001:top_face:b9ec9b032ae6' did not resolve any face |
| 3 | exec error: 'Part' object has no attribute 'lobed_profile' |
| 3 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 14) |
| 3 | exec error: 'Part' object has no attribute 'profile_path' |
| 3 | exec error: Part.loft() got an unexpected keyword argument 'upper_radius' |
| 3 | exec error: 'Part' object has no attribute 'hole_on_face' |
| 3 | exec error: 'Part' object has no attribute 'fillet_on_face' |
| 2 | exec error: Part.sketch_on_face() got an unexpected keyword argument 'size' |
| 2 | exec error: 'Part' object has no attribute 'cut_on_face' |
| 2 | exec error: 'Part' object has no attribute 'rectangular_slot' |
| 2 | SyntaxError: invalid syntax. Maybe you meant '==' or ':=' instead of '='? (<unknown>, line 13) |
| 2 | exec error: hole pattern positions must be 2D or 3D sequences |
| 2 | SyntaxError: invalid decimal literal (<unknown>, line 1) |
| 2 | exec error: 'Part' object has no attribute 'history_enclosure' |
| 2 | exec error: Part.shell() got an unexpected keyword argument 'layers' |
| 2 | exec error: 'Part' object has no attribute 'callout' |
| 2 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 13) |
| 2 | exec error: 'Part' object has no attribute 'sketch_on_plate' |
| 2 | exec error: 'Part' object has no attribute 'lofted_solid' |
| 2 | SyntaxError: '[' was never closed (<unknown>, line 8) |
| 2 | exec error: 'FeatureHandle' object has no attribute 'edge_breaks' |
| 2 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 25) |
| 2 | exec error: 'Part' object has no attribute 'threaded_bearing_on_face' |
| 2 | exec error: 'Part' object has no attribute 'face_on_plate' |
| 2 | exec error: 'Part' object has no attribute 'face' |
| 2 | SyntaxError: '(' was never closed (<unknown>, line 25) |
| 2 | SyntaxError: '[' was never closed (<unknown>, line 13) |
| 2 | exec error: 'Part' object has no attribute 'threaded_bearing_plate_on_face' |
| 1 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'sketch' |
| 1 | SyntaxError: unterminated string literal (detected at line 17) (<unknown>, line 17) |
| 1 | exec error: Part.bossed_plate() missing 3 required keyword-only arguments: 'boss_height', 'hole_radius', and 'hole_positions' |
| 1 | exec error: unsupported sketch_on_face profile [[-38.61, -27.75], [38.61, -27.75], [38.61, 27.75], [23.2, 27.75], [23.2, -14.94], [-23.2, -14.94], [-23.2, 27.75], [-38.61, 27.75]] |
| 1 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'positions' |
| 1 | exec error: depth must be positive, got -1.4 |
| 1 | exec error: thickness must resolve to a number, got 'through' |
| 1 | exec error: unsupported sketch_on_face profile [[-27.2, -18.68], [27.2, -18.68], [27.2, 18.68], [-27.2, 18.68]] |
| 1 | exec error: 'FeatureHandle' object has no attribute 'height' |
| 1 | exec error: name 'y' is not defined |
| 1 | exec error: name '__all' is not defined |
| 1 | exec error: 'Part' object has no attribute 'profile_on_face' |
| 1 | exec error: unsupported sketch_on_face profile [[-27.36, -27.84], [-31.5, -27.84], [-31.5, 25.08], [12.66, 25.08], [12.66, 27.84], [31.5, 27.84]] |
| 1 | exec error: Part.shell() got an unexpected keyword argument 'faces' |
| 1 | exec error: unsupported extrude_on_face operation 'extra' |
| 1 | SyntaxError: unterminated string literal (detected at line 18) (<unknown>, line 18) |
| 1 | exec error: 'Part' object has no attribute 'profile_face_on_top' |
| 1 | exec error: 'Part' object has no attribute 'profile_revolve' |
| 1 | SyntaxError: unterminated string literal (detected at line 11) (<unknown>, line 11) |
| 1 | exec error: 'lobed_gasket_profile_plate_width' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 11) |
| 1 | exec error: unsupported sketch_on_face profile [[-26.46, -24.65], [26.46, -24.65], [26.46, 24.65], [16.34, 24.65], [16.34, -13.91], [-16.34, -13.91], [-16.34, 24.65], [-26.46, 24.65]] |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'height' |
| 1 | no `part` variable after execution |
| 1 | exec error: 'Part' object has no attribute 'join' |
| 1 | exec error: 'Part' object has no attribute 'extrude_sweep' |
| 1 | exec error: 'Part' object has no attribute 'profile_sketch' |
| 1 | exec error: 'Part' object has no attribute 'threaded_bearing_hole' |
| 1 | exec error: 'Part' object has no attribute 'rectangular_fillet' |
| 1 | exec error: 'Part' object has no attribute 'threaded_bearing_plate_on_top' |
| 1 | exec error: 'Part' object has no attribute 'offset_face' |
| 1 | exec error: thickness must resolve to a number, got 'thick' |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 17) |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 21) |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 18) |
| 1 | exec error: 'Part' object has no attribute 'offset_profile' |
| 1 | exec error: 'radius' |
| 1 | exec error: Part.rotate() got an unexpected keyword argument 'angle' |
| 1 | exec error: 'Part' object has no attribute 'extrude_face' |
| 1 | exec error: Part.pin_cluster() got an unexpected keyword argument 'width' |
| 1 | exec error: 'Part' object has no attribute 'threaded_bearing_contract' |
| 1 | exec error: topology reference 'sweep_tube_001:top_face:b2f164f681f5' did not resolve any face |
| 1 | exec error: 'TopologyReference' object is not subscriptable |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 9) |
| 1 | exec error: hole depth must be a number or 'through' |
| 1 | SyntaxError: invalid syntax. Maybe you meant '==' or ':=' instead of '='? (<unknown>, line 1) |
| 1 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'position' |
| 1 | exec error: Part.revolved_bushing() got an unexpected keyword argument 'rev_radius' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 20) |
| 1 | exec error: unsupported sketch_on_face profile [[-31.26, -24.85], [31.26, -24.85], [31.26, 24.85], [18.81, 24.85], [18.81, -13.51], [-18.81, -13.51], [-18.81, 24.85], [-31.26, 24.85]] |
| 1 | exec error: 'Part' object has no attribute 'rectangular_fill' |
| 1 | exec error: 'Part' object has no attribute 'box_constraint' |
| 1 | SyntaxError: f-string: unmatched '[' (<unknown>, line 18) |
| 1 | exec error: offset must be a 3D sequence |
| 1 | exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'jaw_position' |
| 1 | exec error: Part.sphere() got an unexpected keyword argument 'height' |
| 1 | SyntaxError: unmatched ')' (<unknown>, line 3) |
| 1 | exec error: 'Part' object has no attribute 'profile_offset' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_edges' |
| 1 | exec error: unsupported sketch_on_face profile [[-38.08, -22.44], [38.08, -22.44], [38.08, 22.44], [22.19, 22.44], [22.19, -12.32], [-22.19, -12.32], [-22.19, 22.44], [-38.08, 22.44]] |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 16) |
| 1 | exec error: 'FeatureHandle' object has no attribute 'edge' |
| 1 | exec error: unsupported sketch_on_face profile [[-34.64, -24.65], [34.64, -24.65], [34.64, 24.65], [20.31, 24.65], [20.31, -13.06], [-20.31, -13.06], [-20.31, 24.65], [-34.64, 24.65]] |
| 1 | exec error: 'Part' object has no attribute 'profile_join' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 15) |
| 1 | exec error: Part.loft() got an unexpected keyword argument 'profile' |
| 1 | exec error: unsupported sketch_on_face profile [[-39.52, -26.38], [39.52, -26.38], [39.52, 26.38], [23.11, 26.38], [23.11, -14.49], [-23.11, -14.49], [-23.11, 26.38], [-39.52, 26.38]] |
| 1 | SyntaxError: unmatched ')' (<unknown>, line 13) |
| 1 | exec error: 'Part' object has no attribute 'hole' |
| 1 | exec error: 'hole_length' |
| 1 | exec error: Part.extrude() got an unexpected keyword argument 'boss_profile' |
| 1 | exec error: mirror: axis must be 'X', 'Y', or 'Z' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_edge_pattern' |
| 1 | exec error: 'list' object has no attribute 'strip' |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'radius' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'front_face' |
| 1 | exec error: unsupported sketch_on_face profile [[-31.96, -24.11], [31.96, -24.11], [31.96, 24.11], [-31.96, 24.11]] |
| 1 | exec error: Part.sketch_polygon() got an unexpected keyword argument 'vertices' |
| 1 | SyntaxError: unterminated string literal (detected at line 14) (<unknown>, line 14) |
| 1 | SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 5) |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'thread_segments' |
| 1 | exec error: 'Part' object has no attribute 'section' |
| 1 | exec error: 'Part' object has no attribute 'circular_arc' |
| 1 | exec error: 'Part' object has no attribute 'face_sketch' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'edge_21' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'center' |
| 1 | exec error: 'Part' object has no attribute 'history_profile' |
| 1 | SyntaxError: unmatched ']' (<unknown>, line 3) |
| 1 | exec error: keyword argument repeated: offsets (<candidate>, line 19) |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_edge' |

### point / A

Scoreable=1267; target-present=2500; missing-target=0; kernel-crashes=0; export-but-unscoreable=27; gate/geometry flag-mismatch cases=0; CD>1000 scored cases=2.
First failure stages: `{"exec_ok_failure": 1121, "post_export_geometry_failure": 27, "scoreable": 1267, "step_export_ok_failure": 21, "syntax_ok_failure": 64}`.
Geometry-run gate counts: `{"build_ok": 1315, "exec_ok": 1315, "solid_valid": 1315, "step_export_ok": 1294, "syntax_ok": 2436}`.
Native gate runtime seconds=202.48; native geometry Python=3.11.11. Geometry runtime is not separately measured by this script; no wall-time estimate is invented.
Retained last-attempt geometry resume messages: `[]`. The last log is not a complete independent retry history.

| Count | Exact error |
| ---: | --- |
| 224 | exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face |
| 72 | exec error: mirror: plane must be 'YZ', 'XZ', or 'XY' |
| 62 | exec error: Part.plate() got an unexpected keyword argument 'length' |
| 33 | exec error: Part.box() got an unexpected keyword argument 'thickness' |
| 32 | exec error: Part.circular_pattern() got an unexpected keyword argument 'radius' |
| 31 | exec error: 'Part' object has no attribute 'sweep_profile' |
| 28 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'position' |
| 27 | point cloud sampling failed on generated part |
| 25 | exec error: 'width' |
| 23 | exec error: 'Part' object has no attribute 'rectangular_solid_slot' |
| 21 | STEP export error: OCCT build failed |
| 21 | exec error: 'Part' object has no attribute 'boss_profile' |
| 20 | SyntaxError: unterminated string literal (detected at line 9) (<unknown>, line 9) |
| 20 | exec error: 'Part' object has no attribute 'sweep_annular_path' |
| 17 | exec error: target must be a TopologyReference from a FeatureHandle |
| 17 | exec error: 'Part' object has no attribute 'sweep_pipe_bracket' |
| 15 | exec error: parameter 'path_length' already exists |
| 15 | exec error: Part.shell() got an unexpected keyword argument 'sides' |
| 14 | exec error: Part.chamfer() got an unexpected keyword argument 'length' |
| 13 | SyntaxError: invalid syntax (<unknown>, line 1) |
| 13 | exec error: Part.loft() got an unexpected keyword argument 'target' |
| 12 | exec error: 'Part' object has no attribute 'loft_on_face' |
| 11 | exec error: 'Part' object has no attribute 'box_on_face' |
| 11 | exec error: 'Part' object has no attribute 'foot' |
| 11 | exec error: parameter 'height' already exists |
| 11 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_from' |
| 10 | exec error: Part.torus() got an unexpected keyword argument 'radius' |
| 10 | exec error: extrude_on_face join/add requires height |
| 9 | exec error: Part.pin_cluster() got an unexpected keyword argument 'row_width' |
| 9 | exec error: Part.loft_adapter() got an unexpected keyword argument 'profile' |
| 9 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'layer' |
| 8 | exec error: 'Part' object has no attribute 'profile_set' |
| 7 | exec error: 'Part' object has no attribute 'boss_plate' |
| 7 | exec error: Part.circular_pattern() got an unexpected keyword argument 'center' |
| 7 | exec error: parameter 'fillet_radius' already exists |
| 7 | exec error: Part.wedge() got an unexpected keyword argument 'length' |
| 7 | exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float' |
| 7 | exec error: 'lower_slot_height' |
| 7 | exec error: Part.sweep_tube() got an unexpected keyword argument 'thickness' |
| 7 | exec error: target must be a FeatureHandle |
| 6 | exec error: 'Part' object has no attribute 'boss_plate_on_plate' |
| 6 | exec error: 'Part' object has no attribute 'footing' |
| 6 | exec error: topology reference 'join_002:top_face:323af5d41048' did not resolve any face |
| 6 | exec error: Part.plate() got an unexpected keyword argument 'hole_radius' |
| 6 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'offset' |
| 5 | exec error: 'Part' object has no attribute 'rectangular_cut' |
| 5 | exec error: Part.hole_pattern() got an unexpected keyword argument 'position' |
| 5 | exec error: 'Part' object has no attribute 'face_cut_on_face' |
| 5 | exec error: height must resolve to a number, got 'through' |
| 5 | exec error: 'Part' object has no attribute 'slot_pattern' |
| 5 | exec error: 'Part' object has no attribute 'loft_profile' |
| 5 | exec error: Part.hole_pattern() missing 1 required keyword-only argument: 'target' |
| 5 | exec error: 'Part' object has no attribute 'profile_cut' |
| 5 | exec error: topology reference 'cut_001:top_face:e6c86e3e481d' did not resolve any face |
| 4 | exec error: parameter 'boss_height' already exists |
| 4 | exec error: Part.cylinder() got an unexpected keyword argument 'length' |
| 4 | SyntaxError: unmatched ']' (<unknown>, line 1) |
| 4 | exec error: 'Part' object has no attribute 'clipped_offset_sphere' |
| 4 | exec error: 'Part' object has no attribute 'face' |
| 4 | exec error: 'Part' object has no attribute 'fin_base' |
| 4 | exec error: 'Part' object has no attribute 'face_extrude' |
| 4 | exec error: 'Part' object has no attribute 'extrude_on_sketch' |
| 4 | exec error: direction must be 'inward' or 'outward' |
| 4 | exec error: Part.linear_pattern() got an unexpected keyword argument 'offset' |
| 4 | SyntaxError: unterminated string literal (detected at line 10) (<unknown>, line 10) |
| 4 | exec error: 'Part' object has no attribute 'focal_length_foot' |
| 3 | exec error: Part.rectangular_pocket() missing 1 required keyword-only argument: 'target' |
| 3 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 21) |
| 3 | exec error: 'Part' object has no attribute 'lofted_flange' |
| 3 | exec error: 'Part' object has no attribute 'hole_on_face' |
| 3 | exec error: 'Part' object has no attribute 'rectangular_slot' |
| 3 | exec error: points[] must be a 2D sequence |
| 3 | exec error: Part.boolean_cut() got an unexpected keyword argument 'depth' |
| 3 | exec error: 'Part' object has no attribute 'boss_on_plate' |
| 3 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'height' |
| 3 | exec error: 'Part' object has no attribute 'fin' |
| 3 | exec error: Part.cone() got an unexpected keyword argument 'height_top' |
| 3 | exec error: Part.rotate() got an unexpected keyword argument 'angle' |
| 3 | exec error: 'Part' object has no attribute 'cylinder_profile' |
| 3 | exec error: Parameters.add() got an unexpected keyword argument 'options' |
| 3 | exec error: bad operand type for unary -: 'ParameterRef' |
| 3 | exec error: 'Part' object has no attribute 'profile_on_plate' |
| 2 | exec error: loft requires at least two profile features |
| 2 | exec error: Part.loft() got an unexpected keyword argument 'lower_radius' |
| 2 | exec error: Part.sensor_mount_plate() got an unexpected keyword argument 'base_plate' |
| 2 | exec error: 'Part' object has no attribute 'ftpoi' |
| 2 | exec error: threaded_hole_on_face: offset_mode must be 'world' or 'face'. Prefer offset_world=(x, y, z) for world offsets or offset_uv=(u, v) for face-local offsets. |
| 2 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'offset' |
| 2 | exec error: 'Part' object has no attribute 'fit' |
| 2 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_guides' |
| 2 | exec error: 'Part' object has no attribute 'focal_profile_foot' |
| 2 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_position' |
| 2 | exec error: 'Part' object has no attribute 'plate_plate_mounted_plate' |
| 2 | exec error: Part.sweep_tube() got an unexpected keyword argument 'pipe_radius' |
| 2 | exec error: Part.sketch_polygon() got an unexpected keyword argument 'vertices' |
| 2 | exec error: Part.loft() got an unexpected keyword argument 'targets' |
| 2 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_reference' |
| 2 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 20) |
| 2 | exec error: 'length' |
| 2 | exec error: 'Part' object has no attribute 'sweep_annular_bottom' |
| 2 | exec error: Part.bossed_plate() got an unexpected keyword argument 'chamfer_distance' |
| 2 | exec error: topology reference 'revolve_001:top_face:d95ca6795e31' did not resolve any face |
| 2 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_frequency' |
| 2 | exec error: 'Part' object has no attribute 'plate_motor_mount_plate' |
| 2 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_plan' |
| 2 | exec error: 'Part' object has no attribute 'boss_shape' |
| 2 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'major_radius' |
| 2 | exec error: 'FeatureHandle' object has no attribute 'face' |
| 2 | exec error: 'Part' object has no attribute 'profile_cut_on_profile' |
| 2 | exec error: 'Part' object has no attribute 'vector' |
| 2 | SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 1) |
| 2 | exec error: Part.offset() got an unexpected keyword argument 'offset_distance' |
| 2 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'profile' |
| 2 | exec error: unsupported operand type(s) for /: 'ParameterRef' and 'float' |
| 2 | exec error: Part.sweep_tube() got an unexpected keyword argument 'height' |
| 2 | exec error: Part.box() got an unexpected keyword argument 'target' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'length' |
| 1 | exec error: Part.shelled_cover_plate() got an unexpected keyword argument 'hole_offsets' |
| 1 | exec error: 'Part' object has no attribute 'hole' |
| 1 | exec error: 'slot_depth' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 32) |
| 1 | exec error: 'Part' object has no attribute 'revolve_on_face' |
| 1 | exec error: topology reference 'cut_002:top_face:d7e817b6f02b' did not resolve any face |
| 1 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'semantic_profile' |
| 1 | exec error: 'Part' object has no attribute 'loft_on_x' |
| 1 | exec error: 'Part' object has no attribute 'extrude_face_on_face' |
| 1 | exec error: 'Part' object has no attribute 'rectangular_bosses' |
| 1 | exec error: Part.extrude() got an unexpected keyword argument 'operation' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 15) |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 13) |
| 1 | exec error: name 'fillet_profile' is not defined |
| 1 | exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'offset_x' |
| 1 | exec error: Part.boolean_join() got an unexpected keyword argument 'offset' |
| 1 | exec error: Part.threaded_hole_on_face() missing 1 required keyword-only argument: 'depth' |
| 1 | exec error: 'path_width' |
| 1 | exec error: 'Part' object has no attribute 'extrude_add' |
| 1 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'lower_width' |
| 1 | exec error: topology reference 'loft_001:top_face:b95a905e855a' did not resolve any face |
| 1 | exec error: 'Part' object has no attribute 'rectangular_cutout' |
| 1 | exec error: 'Part' object has no attribute 'lofted_transition_bracket' |
| 1 | exec error: extrude_on_face cut requires depth |
| 1 | exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'profile_type' |
| 1 | exec error: 'Part' object has no attribute 'ftp_profile_footprint' |
| 1 | SyntaxError: unterminated string literal (detected at line 29) (<unknown>, line 29) |
| 1 | exec error: Parameters.add() got an unexpected keyword argument 'choices' |
| 1 | exec error: 'Part' object has no attribute 'sweep_flange' |
| 1 | exec error: 'Part' object has no attribute 'sketch_boss' |
| 1 | SyntaxError: invalid syntax (<unknown>, line 2) |
| 1 | exec error: 'Part' object has no attribute 'sweep_on_path' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '{' (<unknown>, line 12) |
| 1 | exec error: Part.pin_cluster() got an unexpected keyword argument 'step' |
| 1 | exec error: 'Part' object has no attribute 'foot_profile' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 23) |
| 1 | no `part` variable after execution |
| 1 | exec error: Part.extrude() missing 1 required keyword-only argument: 'height' |
| 1 | exec error: 'Part' object has no attribute 'ftpocket' |
| 1 | SyntaxError: unterminated string literal (detected at line 14) (<unknown>, line 14) |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 22) |
| 1 | exec error: Part.hole_pattern() got an unexpected keyword argument 'offset' |
| 1 | exec error: 'Part' object has no attribute 'profile_point' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'profile_1' |
| 1 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'step' |
| 1 | exec error: depth must resolve to a number, got 'through' |
| 1 | exec error: Parameters.add() got an unexpected keyword argument 'category' |
| 1 | exec error: name 'box_1' is not defined |
| 1 | exec error: 'Part' object has no attribute 'magnet_on_face' |
| 1 | exec error: 'Part' object has no attribute 'footprint' |
| 1 | SyntaxError: unterminated string literal (detected at line 21) (<unknown>, line 21) |
| 1 | exec error: 'upper_slot_depth' |
| 1 | exec error: 'Part' object has no attribute 'patterned_feature_plate' |
| 1 | exec error: 'Part' object has no attribute 'loft_on_x_axis' |
| 1 | SyntaxError: unterminated string literal (detected at line 24) (<unknown>, line 24) |
| 1 | exec error: name 'holes' is not defined |
| 1 | exec error: 'list' object has no attribute 'strip' |
| 1 | exec error: 'Part' object has no attribute 'face_extrude_cut' |
| 1 | exec error: 'Part' object has no attribute 'orthogonal_foot_profile' |
| 1 | exec error: 'Part' object has no attribute 'lofted_transition' |
| 1 | exec error: Part.cone() got an unexpected keyword argument 'over_radius' |
| 1 | exec error: Part.profile_cut_on_face() missing 1 required keyword-only argument: 'depth' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 28) |
| 1 | exec error: Part.sensor_mount_plate() got an unexpected keyword argument 'plate_radius' |
| 1 | exec error: name 'param' is not defined |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_points' |
| 1 | SyntaxError: cannot assign to literal (<unknown>, line 1) |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'thread_pattern' |
| 1 | exec error: 'Part' object has no attribute 'profile_profile' |
| 1 | exec error: Part.boolean_cut() got an unexpected keyword argument 'profile' |
| 1 | SyntaxError: unterminated string literal (detected at line 12) (<unknown>, line 12) |
| 1 | exec error: unsupported operand type(s) for *: 'ParameterRef' and 'ParameterRef' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 22) |
| 1 | exec error: 'Part' object has no attribute 'flange' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 25) |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_inner_edges' |
| 1 | exec error: hole pattern positions must be 2D or 3D sequences |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'flange_radius' |
| 1 | exec error: 'hole_width' |
| 1 | exec error: 'Part' object has no attribute 'mounting_block_bracket' |
| 1 | exec error: 'Part' object has no attribute 'move' |
| 1 | exec error: 'Part' object has no attribute 'flange_on_face' |
| 1 | exec error: 'threaded_bearing_width' |

### point / B

Scoreable=1188; target-present=2500; missing-target=0; kernel-crashes=0; export-but-unscoreable=68; gate/geometry flag-mismatch cases=0; CD>1000 scored cases=0.
First failure stages: `{"exec_ok_failure": 706, "post_export_geometry_failure": 68, "scoreable": 1188, "step_export_ok_failure": 102, "syntax_ok_failure": 436}`.
Geometry-run gate counts: `{"build_ok": 1358, "exec_ok": 1358, "solid_valid": 1358, "step_export_ok": 1256, "syntax_ok": 2064}`.
Native gate runtime seconds=686.93; native geometry Python=3.11.11. Geometry runtime is not separately measured by this script; no wall-time estimate is invented.
Retained last-attempt geometry resume messages: `[]`. The last log is not a complete independent retry history.

| Count | Exact error |
| ---: | --- |
| 370 | SyntaxError: unmatched ']' (<unknown>, line 1) |
| 102 | STEP export error: OCCT build failed |
| 68 | point cloud sampling failed on generated part |
| 46 | exec error: Part.sketch_on_face() got an unexpected keyword argument 'face' |
| 45 | exec error: 'lower_radius' |
| 40 | exec error: Part.circular_pattern() got an unexpected keyword argument 'radius' |
| 39 | exec error: topology reference 'join_002:top_face:323af5d41048' did not resolve any face |
| 35 | exec error: Part.plate() got an unexpected keyword argument 'length' |
| 29 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'profile' |
| 26 | exec error: 'Part' object has no attribute 'extrude_profile' |
| 24 | exec error: mirror: plane must be 'YZ', 'XZ', or 'XY' |
| 22 | exec error: 'Part' object has no attribute 'join' |
| 19 | exec error: target must be a FeatureHandle |
| 17 | exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'length' |
| 15 | exec error: topology reference 'revolve_001:top_face:d95ca6795e31' did not resolve any face |
| 13 | SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 1) |
| 13 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'height' |
| 13 | exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face |
| 12 | exec error: 'Part' object has no attribute 'extrude_solid' |
| 12 | exec error: Part.hole_pattern() got an unexpected keyword argument 'position' |
| 12 | exec error: 'Part' object has no attribute 'box_constraint' |
| 12 | exec error: 'Part' object has no attribute 'rectangular_pocket_profile' |
| 12 | exec error: 'Part' object has no attribute 'move' |
| 11 | SyntaxError: invalid syntax (<unknown>, line 1) |
| 10 | exec error: 'Part' object has no attribute 'threaded_bearing_hole' |
| 9 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 16) |
| 8 | exec error: 'Part' object has no attribute 'box_on_face' |
| 8 | exec error: 'Part' object has no attribute 'rectangular_slot' |
| 8 | exec error: Part.sketch_on_face() got an unexpected keyword argument 'closed' |
| 8 | SyntaxError: unterminated string literal (detected at line 18) (<unknown>, line 18) |
| 8 | exec error: bad operand type for unary -: 'ParameterRef' |
| 7 | exec error: Part.wedge() got an unexpected keyword argument 'width' |
| 6 | exec error: depth must be positive, got -9.18 |
| 6 | exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float' |
| 6 | exec error: target must be a TopologyReference from a FeatureHandle |
| 6 | exec error: 'Part' object has no attribute 'boss_profile' |
| 6 | exec error: points[] must be a 2D sequence |
| 6 | exec error: 'width' |
| 5 | exec error: Part.shell() got an unexpected keyword argument 'layers' |
| 5 | exec error: Part.box() got an unexpected keyword argument 'thickness' |
| 5 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'min_length' |
| 5 | exec error: Part.boolean_cut() got an unexpected keyword argument 'depth' |
| 5 | SyntaxError: unterminated string literal (detected at line 17) (<unknown>, line 17) |
| 4 | exec error: 'Part' object has no attribute 'threaded_bearing_contract' |
| 4 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 18) |
| 4 | exec error: topology reference 'chamfer_001:top_outer_edges:1c8e3f3146f4' did not resolve any edge_set |
| 4 | exec error: boss_center must be a 2D sequence |
| 4 | exec error: Part.sketch_polygon() got an unexpected keyword argument 'vertices' |
| 3 | exec error: 'Part' object has no attribute 'boss_on_plate' |
| 3 | exec error: 'FeatureHandle' object has no attribute 'top_edge_breaks' |
| 3 | exec error: unsupported operand type(s) for +: 'ParameterRef' and 'ParameterRef' |
| 3 | exec error: 'Part' object has no attribute 'threaded_bearing_plate' |
| 3 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'radius' |
| 3 | exec error: hole depth must be a number or 'through' |
| 3 | exec error: 'Part' object has no attribute 'callout_on_face' |
| 3 | exec error: 'Part' object has no attribute 'profile_on_face' |
| 3 | exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'jaw_spacing' |
| 3 | exec error: extrude_on_face join/add requires height |
| 3 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_reference' |
| 2 | exec error: 'Part' object has no attribute 'bosses' |
| 2 | exec error: 'Part' object has no attribute 'profile_revolve' |
| 2 | SyntaxError: '[' was never closed (<unknown>, line 11) |
| 2 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'positions' |
| 2 | exec error: topology reference 'hole_001:top_face:9014e73e3f7b' did not resolve any face |
| 2 | exec error: 'Part' object has no attribute 'text' |
| 2 | exec error: Part.loft() got an unexpected keyword argument 'target' |
| 2 | exec error: topology reference 'fillet_001:top_outer_edges:4a047842f5e8' did not resolve any edge_set |
| 2 | exec error: 'Part' object has no attribute 'boolean_select' |
| 2 | exec error: Part.sketch_circle() got an unexpected keyword argument 'position' |
| 2 | exec error: 'Part' object has no attribute 'extrude_sweep' |
| 2 | exec error: topology reference 'cut_001:top_face:e6c86e3e481d' did not resolve any face |
| 2 | exec error: Part.clamp_pad_plate() missing 1 required keyword-only argument: 'jaw_offset_x' |
| 2 | exec error: Part.pin_cluster() got an unexpected keyword argument 'row_width' |
| 2 | exec error: extrude_on_face cut requires depth |
| 2 | exec error: 'Part' object has no attribute 'section' |
| 2 | SyntaxError: cannot assign to literal (<unknown>, line 1) |
| 2 | exec error: 'Part' object has no attribute 'rectangular_cut' |
| 2 | exec error: object of type 'float' has no len() |
| 2 | exec error: hole pattern positions must be 2D or 3D sequences |
| 2 | exec error: 'Part' object has no attribute 'threaded_profile_on_face' |
| 1 | exec error: Part.__init__() got an unexpected keyword argument 'semantic_type' |
| 1 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'length' |
| 1 | exec error: 'list' object has no attribute 'strip' |
| 1 | exec error: 'Part' object has no attribute 'boolean_difference' |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'solid' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_profile' |
| 1 | exec error: 'Part' object has no attribute 'sweep_on_profile' |
| 1 | exec error: Part.extrude() got an unexpected keyword argument 'thickness' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 19) |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 15) |
| 1 | exec error: 'Part' object has no attribute 'thickness' |
| 1 | exec error: unsupported sketch_on_face profile [[0.0, 0.0], [14.44, 0.0], [14.44, 3.14], [0.0, 3.14]] |
| 1 | exec error: unsupported sketch_on_face profile [[-47.2, -16.55], [47.2, -16.55], [47.2, 16.55], [25.1, 16.55], [25.1, -10.01]] |
| 1 | exec error: 'Part' object has no attribute 'profile_offset' |
| 1 | exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'width' |
| 1 | exec error: unsupported sketch_on_face profile [[-12.14, -10.56], [12.14, -10.56], [12.14, 10.56], [-12.14, 10.56]] |
| 1 | exec error: Part.linear_pattern() missing 1 required keyword-only argument: 'step' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_center' |
| 1 | exec error: name 'parameters' is not defined |
| 1 | exec error: 'Part' object has no attribute 'fillet_on_face' |
| 1 | exec error: 'Part' object has no attribute 'extrude_rectangle_pocket' |
| 1 | exec error: Part.rail_mount_plate() got an unexpected keyword argument 'boss_radius' |
| 1 | exec error: unsupported sketch_on_face profile ['rectangle', [ParameterRef(name='boss_width', value=23.1, min=8.0, max=44.0, expression='width * 0.308', unit=None, semantic_type='boss_width'), ParameterRef(name='boss_height', value=10.1, min=6.0, max=28.0, expression='height * 0.28', unit=None, semantic_type='boss_height')]] |
| 1 | exec error: topology reference 'cut_003:top_face:bed62e2cb71a' did not resolve any face |
| 1 | exec error: Part.loft() got an unexpected keyword argument 'upper_radius' |
| 1 | exec error: topology reference 'sweep_tube_001:top_face:b2f164f681f5' did not resolve any face |
| 1 | SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<unknown>, line 14) |
| 1 | exec error: unsupported operand type(s) for +: 'ParameterRef' and 'float' |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'min' |
| 1 | exec error: 'Part' object has no attribute 'profile_from_sketch' |
| 1 | exec error: topology reference 'hole_002:top_outer_edges:e747732acb4e' did not resolve any edge_set |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 9) |
| 1 | exec error: length must resolve to a number, got 'prompt_value' |
| 1 | exec error: 'Part' object has no attribute 'extrude_rectangle_profile' |
| 1 | exec error: 'Part' object has no attribute 'offset_profile' |
| 1 | exec error: unsupported sketch_on_face profile [[-35.28, -19.12], [35.28, -19.12], [35.28, 19.12], [20.2, 19.12], [20.2, -10.2], [-20.2, -10.2], [-20.2, 19.12], [-35.28, 19.12]] |
| 1 | exec error: 'FeatureHandle' object has no attribute 'height' |
| 1 | exec error: Part.__init__() got an unexpected keyword argument 'width' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'profile' |
| 1 | exec error: 'Part' object has no attribute 'lofted_solid' |
| 1 | exec error: 'web_angle' |
| 1 | exec error: offset must be a 3D sequence |
| 1 | exec error: 'bolt_hole_radius' |
| 1 | exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'jaw_center' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_edge_pattern' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 11) |
| 1 | SyntaxError: cannot assign to attribute here. Maybe you meant '==' instead of '='? (<unknown>, line 1) |
| 1 | exec error: 'FeatureHandle' object has no attribute 'holes_from_edges' |
| 1 | exec error: 'height' |
| 1 | exec error: 'hole_radius' |
| 1 | SyntaxError: invalid syntax. Maybe you meant '==' or ':=' instead of '='? (<unknown>, line 15) |
| 1 | exec error: 'Part' object has no attribute 'box_wall' |
| 1 | exec error: 'Part' object has no attribute 'rectangular_slot_on_face' |
| 1 | exec error: 'boss_top_face' |
| 1 | exec error: Part.chamfer() got an unexpected keyword argument 'radius' |
| 1 | exec error: 'Part' object has no attribute 'section_profile' |
| 1 | exec error: topology reference 'pocket_001:edges:dc4d4c7108bd' did not resolve any edge_set |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'thread_type' |
| 1 | exec error: depth must be positive, got -2.24 |
| 1 | exec error: 'Part' object has no attribute 'cut_on_face' |
| 1 | exec error: Part.sensor_mount_plate() got an unexpected keyword argument 'hole_offsets' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_edge' |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 7) |
| 1 | exec error: Part.revolved_bushing() got an unexpected keyword argument 'height' |
| 1 | exec error: 'Part' object has no attribute 'profile_face_on_face' |
| 1 | exec error: hex() takes exactly one argument (2 given) |
| 1 | exec error: 'lower_flange_thickness' |
| 1 | SyntaxError: invalid syntax (<unknown>, line 25) |
| 1 | exec error: unsupported sketch_on_face profile ['rectangle', [ParameterRef(name='boss_width', value=28.1, min=8.0, max=44.0, expression='width * 0.307', unit=None, semantic_type='boss_width'), ParameterRef(name='boss_height', value=10.1, min=6.0, max=28.0, expression='height * 0.26', unit=None, semantic_type='boss_height')]] |
| 1 | exec error: Part.loft() got an unexpected keyword argument 'profile' |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 25) |
| 1 | exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'min_height' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 13) |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 12) |
| 1 | exec error: Parameters.add() got an unexpected keyword argument 'chamfer_distance' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_edges' |
| 1 | exec error: 'Part' object has no attribute 'path_follow' |
| 1 | exec error: 'Part' object has no attribute 'edge_path' |
| 1 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'width' |
| 1 | exec error: depth must be positive, got -9.78 |
| 1 | exec error: Part.revolved_bushing() got an unexpected keyword argument 'radius' |
| 1 | exec error: Part.bossed_plate() missing 2 required keyword-only arguments: 'hole_radius' and 'hole_positions' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'radius' |

### text / A

Scoreable=1233; target-present=2500; missing-target=0; kernel-crashes=0; export-but-unscoreable=12; gate/geometry flag-mismatch cases=0; CD>1000 scored cases=3.
First failure stages: `{"exec_ok_failure": 1198, "post_export_geometry_failure": 12, "scoreable": 1233, "step_export_ok_failure": 16, "syntax_ok_failure": 41}`.
Geometry-run gate counts: `{"build_ok": 1261, "exec_ok": 1261, "solid_valid": 1261, "step_export_ok": 1245, "syntax_ok": 2459}`.
Native gate runtime seconds=252.055; native geometry Python=3.11.11. Geometry runtime is not separately measured by this script; no wall-time estimate is invented.
Retained last-attempt geometry resume messages: `[]`. The last log is not a complete independent retry history.

| Count | Exact error |
| ---: | --- |
| 73 | exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face |
| 68 | exec error: topology reference 'revolve_001:top_face:d95ca6795e31' did not resolve any face |
| 56 | exec error: 'width' |
| 47 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'position' |
| 44 | exec error: target must be a TopologyReference from a FeatureHandle |
| 43 | exec error: mirror: plane must be 'YZ', 'XZ', or 'XY' |
| 29 | exec error: Part.plate() got an unexpected keyword argument 'length' |
| 26 | exec error: target must be a FeatureHandle |
| 25 | exec error: 'Part' object has no attribute 'stepped_profile_mount' |
| 25 | exec error: 'Part' object has no attribute 'sweep_profile' |
| 24 | exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float' |
| 22 | exec error: 'Part' object has no attribute 'lobed_gasket_profile' |
| 21 | exec error: Part.box() got an unexpected keyword argument 'thickness' |
| 19 | SyntaxError: invalid syntax (<unknown>, line 1) |
| 17 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path_offset_y' |
| 16 | exec error: topology reference 'join_002:top_face:323af5d41048' did not resolve any face |
| 16 | exec error: 'Part' object has no attribute 'move' |
| 16 | STEP export error: OCCT build failed |
| 16 | exec error: 'Part' object has no attribute 'profile_set' |
| 15 | exec error: parameter 'path_length' already exists |
| 13 | exec error: 'Part' object has no attribute 'sweep_pipe_bracket' |
| 12 | exec error: Part.chamfer() got an unexpected keyword argument 'length' |
| 12 | point cloud sampling failed on generated part |
| 12 | exec error: 'Part' object has no attribute 'rectangular_slot' |
| 11 | exec error: 'Part' object has no attribute 'lofted_flange' |
| 11 | exec error: 'Part' object has no attribute 'loft_on_face' |
| 11 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'offset' |
| 10 | exec error: Part.circular_pattern() got an unexpected keyword argument 'radius' |
| 10 | exec error: 'Part' object has no attribute 'face_add_on_profile' |
| 10 | exec error: 'length' |
| 10 | exec error: Part.boolean_cut() got an unexpected keyword argument 'depth' |
| 9 | exec error: extrude_on_face join/add requires height |
| 8 | exec error: Part.sweep_tube() got an unexpected keyword argument 'width' |
| 8 | exec error: Part.loft() got an unexpected keyword argument 'target' |
| 8 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_from' |
| 8 | exec error: Part.standoff_array_plate() got an unexpected keyword argument 'hole_offset_x' |
| 8 | exec error: offset must be a 3D sequence |
| 8 | exec error: Part.extrude() got an unexpected keyword argument 'operation' |
| 7 | exec error: 'Part' object has no attribute 'bosses' |
| 7 | exec error: Part.standoff_array_plate() got an unexpected keyword argument 'hole_spacing' |
| 7 | exec error: Part.revolved_bushing() got an unexpected keyword argument 'section_radius' |
| 7 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path_width' |
| 7 | exec error: 'Part' object has no attribute 'trapzoid_profile_foot' |
| 6 | exec error: 'Part' object has no attribute 'bolt_hole_pattern' |
| 6 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'semantic_profile' |
| 6 | exec error: topology reference 'cut_001:top_face:e6c86e3e481d' did not resolve any face |
| 6 | exec error: Part.plate() got an unexpected keyword argument 'hole_radius' |
| 5 | exec error: 'Part' object has no attribute 'mounting_plate' |
| 5 | exec error: 'thickness' |
| 5 | exec error: 'Part' object has no attribute 'boss_profile' |
| 5 | exec error: Part.hole_pattern() got an unexpected keyword argument 'offset' |
| 5 | exec error: Part.bossed_plate() got an unexpected keyword argument 'chamfer_distance' |
| 5 | exec error: Part.box() got an unexpected keyword argument 'target' |
| 5 | exec error: Part.sweep_tube() got an unexpected keyword argument 'thickness' |
| 4 | exec error: 'height' |
| 4 | exec error: Parameters.add() got an unexpected keyword argument 'category' |
| 4 | exec error: 'Part' object has no attribute 'hole' |
| 4 | exec error: 'Part' object has no attribute 'extruded_lug_profile' |
| 4 | exec error: Part.cylinder() got an unexpected keyword argument 'length' |
| 4 | exec error: parameter 'flange_thickness' already exists |
| 4 | SyntaxError: unmatched ']' (<unknown>, line 1) |
| 4 | exec error: 'Part' object has no attribute 'hole_radius' |
| 4 | exec error: unsupported operand type(s) for /: 'ParameterRef' and 'float' |
| 4 | exec error: 'Part' object has no attribute 'lobed_hole_profile' |
| 4 | exec error: 'lug_radius' |
| 4 | exec error: 'Part' object has no attribute 'ftfoot' |
| 3 | exec error: 'Part' object has no attribute 'sweep_annular_path' |
| 3 | exec error: 'Part' object has no attribute 'box_on_face' |
| 3 | exec error: 'Part' object has no attribute 'clamp_pad_bracket' |
| 3 | exec error: 'Part' object has no attribute 'foot_plate' |
| 3 | exec error: 'Part' object has no attribute 'extrude_on_profile' |
| 3 | exec error: 'FeatureHandle' object has no attribute 'profile' |
| 3 | exec error: Part.cylinder() got an unexpected keyword argument 'top_radius' |
| 3 | exec error: 'Part' object has no attribute 'sweep_flange' |
| 3 | exec error: parameter 'boss_height' already exists |
| 3 | exec error: 'Part' object has no attribute 'offset_hole' |
| 3 | exec error: 'pocket_depth' |
| 3 | exec error: Part.torus() got an unexpected keyword argument 'radius' |
| 3 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path_offset_x' |
| 3 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'semantic_center' |
| 3 | exec error: 'Part' object has no attribute 'shelled_enclosure' |
| 3 | exec error: unsupported extrude_on_face operation 'extrude' |
| 3 | exec error: 'hole_radius' |
| 3 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'radius' |
| 3 | exec error: 'Part' object has no attribute 'offset_hole_plate' |
| 3 | exec error: 'Part' object has no attribute 'lofted_transition_bracket' |
| 3 | exec error: 'Part' object has no attribute 'face' |
| 3 | exec error: 'Part' object has no attribute 'profile_plain' |
| 3 | exec error: 'Part' object has no attribute 'clipped_sphere' |
| 3 | exec error: parameter 'height' already exists |
| 2 | exec error: 'Part' object has no attribute 'loft_loft_adapter' |
| 2 | exec error: 'Part' object has no attribute 'bossed_flange_plate' |
| 2 | exec error: 'Part' object has no attribute 'face_add' |
| 2 | exec error: Part.cylinder() got an unexpected keyword argument 'thickness' |
| 2 | exec error: 'Part' object has no attribute 'flange' |
| 2 | exec error: Part.extrude() got an unexpected keyword argument 'offset' |
| 2 | exec error: Part.shell() got an unexpected keyword argument 'layers' |
| 2 | exec error: Part.boolean_join() got an unexpected keyword argument 'operation' |
| 2 | exec error: 'Part' object has no attribute 'revolved_hub_mount' |
| 2 | exec error: Part.shelled_cover_plate() got an unexpected keyword argument 'hole_offsets' |
| 2 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'height' |
| 2 | exec error: 'Part' object has no attribute 'foot_profile' |
| 2 | exec error: Part.sweep_tube() got an unexpected keyword argument 'height' |
| 2 | exec error: topology reference 'pocket_001:top_face:6bc5ae6c80c5' did not resolve any face |
| 2 | exec error: 'Part' object has no attribute 'extrude_face_add' |
| 2 | exec error: direction must be 'inward' or 'outward' |
| 2 | exec error: Part.__init__() got an unexpected keyword argument 'min_max_height' |
| 2 | exec error: 'Part' object has no attribute 'profile_plate' |
| 2 | exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'jaw_center' |
| 2 | exec error: Part.loft() got an unexpected keyword argument 'profile' |
| 2 | exec error: Part.sweep_tube() got an unexpected keyword argument 'inner_radius' |
| 2 | exec error: Part.pin_cluster() got an unexpected keyword argument 'offset' |
| 2 | exec error: 'inner_radius' |
| 2 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'offset' |
| 2 | exec error: Part.sweep_tube() missing 1 required keyword-only argument: 'path_mid_length' |
| 2 | exec error: 'Part' object has no attribute 'clamp_jaw' |
| 2 | exec error: 'FeatureHandle' object has no attribute 'edgescatch' |
| 2 | exec error: hole depth must be a number or 'through' |
| 2 | exec error: points[] must be a 2D sequence |
| 2 | exec error: Part.pin_cluster() got an unexpected keyword argument 'spacing' |
| 2 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_reference' |
| 2 | exec error: name 'moved_1' is not defined |
| 2 | exec error: 'Part' object has no attribute 'sweep_tube_bracket' |
| 2 | exec error: Part.__init__() got an unexpected keyword argument 'semantic_type' |
| 2 | exec error: Part.sketch_polygon() got an unexpected keyword argument 'target' |
| 2 | SyntaxError: invalid syntax (<unknown>, line 2) |
| 2 | exec error: 'Part' object has no attribute 'sweep_segments' |
| 2 | exec error: Part.pin_cluster() got an unexpected keyword argument 'pin_radius' |
| 2 | exec error: 'Part' object has no attribute 'sketch_on_plate' |
| 2 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path_mid_height' |
| 1 | exec error: 'shell_thickness' |
| 1 | exec error: Part.extrude() got an unexpected keyword argument 'radius' |
| 1 | exec error: 'Part' object has no attribute 'bossed_flange_pattern' |
| 1 | exec error: topology reference 'mirror_001:top_face:efb86cfa25dd' did not resolve any face |
| 1 | exec error: Part.bossed_plate() got an unexpected keyword argument 'boss_width' |
| 1 | exec error: Part.standoff_array_plate() got an unexpected keyword argument 'standoff_jaw_height' |
| 1 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'semantic_height' |
| 1 | exec error: topology reference 'join_003:top_face:0589a64f06ca' did not resolve any face |
| 1 | exec error: Part.pin_cluster() got an unexpected keyword argument 'radial_offset' |
| 1 | exec error: 'Part' object has no attribute 'face_add_on_top' |
| 1 | exec error: 'Part' object has no attribute 'linear_ribbed_heat_sink_mount' |
| 1 | SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 1) |
| 1 | exec error: 'Part' object has no attribute 'fin' |
| 1 | exec error: 'Part' object has no attribute 'profile' |
| 1 | exec error: Part.ribbed_support_plate() missing 1 required keyword-only argument: 'rib_height' |
| 1 | exec error: 'Part' object has no attribute 'ellipse' |
| 1 | exec error: 'Parameters' object does not support item assignment |
| 1 | exec error: Part.revolved_bushing() got an unexpected keyword argument 'thickness' |
| 1 | SyntaxError: unterminated string literal (detected at line 9) (<unknown>, line 9) |
| 1 | SyntaxError: unmatched ')' (<unknown>, line 19) |
| 1 | exec error: unsupported operand type(s) for \|: 'FeatureHandle' and 'FeatureHandle' |
| 1 | exec error: 'Part' object has no attribute 'boolean_cover' |
| 1 | exec error: 'Part' object has no attribute 'revolve_on_profile' |
| 1 | exec error: unsupported operand type(s) for +: 'FeatureHandle' and 'FeatureHandle' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_edge' |
| 1 | exec error: 'Part' object has no attribute 'profile_cut' |
| 1 | exec error: 'Part' object has no attribute 'trap_profile_foot' |
| 1 | exec error: 'Part' object has no attribute 'extrude_face_on_plate' |
| 1 | exec error: name '半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边半边�' is not defined |
| 1 | exec error: Part.hole_pattern() got an unexpected keyword argument 'distance' |
| 1 | exec error: object of type 'ParameterRef' has no len() |
| 1 | exec error: 'Part' object has no attribute 'offset_hole_pattern' |
| 1 | exec error: parameter 'pocket_width' already exists |
| 1 | exec error: Part.extrude_on_face() missing 1 required keyword-only argument: 'sketch' |
| 1 | exec error: Part.circular_pattern() got an unexpected keyword argument 'offset' |
| 1 | SyntaxError: unterminated string literal (detected at line 11) (<unknown>, line 11) |
| 1 | exec error: 'Part' object has no attribute 'revolve_on_face' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 19) |
| 1 | exec error: 'Part' object has no attribute 'rectangular_solid_slot' |
| 1 | exec error: Part.hole_pattern() missing 1 required keyword-only argument: 'target' |
| 1 | SyntaxError: invalid syntax. Maybe you meant '==' or ':=' instead of '='? (<unknown>, line 20) |
| 1 | exec error: 'Part' object has no attribute 'box_minimum' |
| 1 | exec error: 'Part' object has no attribute 'magnet_on_face' |
| 1 | exec error: Part.hole_pattern() got an unexpected keyword argument 'position' |
| 1 | exec error: 'Part' object has no attribute 'sketch_to_face' |
| 1 | exec error: thickness must resolve to a number, got [3.0, 3.0, 2.0] |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'thread_radius' |
| 1 | exec error: 'Part' object has no attribute 'face_extrude_cut' |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'length' |
| 1 | exec error: 'through_hole_radius' |
| 1 | exec error: 'Part' object has no attribute 'profile_pick' |
| 1 | exec error: 'Part' object has no attribute 'extrude_upper_half' |
| 1 | exec error: Part.extrude() got an unexpected keyword argument 'target' |
| 1 | exec error: Part.revolved_bushing() got an unexpected keyword argument 'width' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 16) |
| 1 | exec error: 'Part' object has no attribute 'offset_hole_on_face' |
| 1 | exec error: 'Part' object has no attribute 'flange_edge_on_top' |
| 1 | exec error: unsupported sketch_on_face profile FeatureHandle(part=<flluma.api.part.Part object at 0x000002950D39C2D0>, feature_id='sketch_001', node=CSGNode(name='lobed_outer_profile', type=Transform)) |
| 1 | exec error: 'Part' object has no attribute 'hole_on_face' |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'section_height' |
| 1 | exec error: 'Part' object has no attribute 'boolean_lock' |
| 1 | exec error: 'TopologyReference' object has no attribute 'top_face' |
| 1 | exec error: Part.torus() got an unexpected keyword argument 'center_hole_radius' |
| 1 | exec error: 'Part' object has no attribute 'face_extrude_on_face' |
| 1 | exec error: 'lower_flange_height' |
| 1 | exec error: 'Part' object has no attribute 'rectangular_pocket_slot_plate' |
| 1 | exec error: topology reference 'sweep_tube_001:top_face:b2f164f681f5' did not resolve any face |
| 1 | SyntaxError: unterminated string literal (detected at line 23) (<unknown>, line 23) |
| 1 | exec error: 'Part' object has no attribute 'plate_mounted_block' |
| 1 | exec error: 'Part' object has no attribute 'intersection_offset_stock' |
| 1 | exec error: 'hole_profile' |
| 1 | exec error: Part.boolean_join() got an unexpected keyword argument 'offset' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 14) |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'thread_depth' |
| 1 | exec error: parameter 'pin_row_width' already exists |
| 1 | exec error: 'Part' object has no attribute 'face_recursive_mount' |
| 1 | exec error: Part.standoff_array_plate() missing 2 required keyword-only arguments: 'standoff_radius' and 'standoff_height' |
| 1 | exec error: 'wall_length' |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'flange_radius' |
| 1 | exec error: 'Part' object has no attribute 'sketch_on_profile' |
| 1 | exec error: Part.clamp_pad_plate() missing 1 required keyword-only argument: 'jaw_offset_x' |
| 1 | exec error: 'Part' object has no attribute 'extrude_profile' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path_segment' |
| 1 | exec error: 'Part' object has no attribute 'extrude_face_on_top' |
| 1 | exec error: Part.bossed_plate() got an unexpected keyword argument 'hole_offset_x' |
| 1 | SyntaxError: invalid syntax. Maybe you meant '==' or ':=' instead of '='? (<unknown>, line 1) |
| 1 | exec error: 'Part' object has no attribute 'boss_top' |
| 1 | SyntaxError: invalid syntax (<unknown>, line 13) |
| 1 | exec error: 'Part' object has no attribute 'l_bracket' |
| 1 | exec error: 'Part' object has no attribute 'cut_on_face' |
| 1 | exec error: 'Part' object has no attribute 'mounting_hole_plate' |
| 1 | exec error: Part.extrude() got an unexpected keyword argument 'width' |
| 1 | exec error: Part.clamp_pad_plate() missing 3 required keyword-only arguments: 'jaw_length', 'jaw_width', and 'jaw_offset_x' |
| 1 | exec error: Part.wedge() got an unexpected keyword argument 'length' |
| 1 | exec error: name 'moved_to' is not defined |
| 1 | exec error: name 'thickness' is not defined |
| 1 | exec error: Part.hole_pattern() got an unexpected keyword argument 'hole_type' |
| 1 | exec error: name 'Profile' is not defined |
| 1 | exec error: Part.mirrored_lug_plate() got an unexpected keyword argument 'lug_offset_y' |
| 1 | exec error: Part.standoff_array_plate() got an unexpected keyword argument 'hole_spacing_x' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'minimal_offset_hole' |
| 1 | exec error: extrude_on_face cut requires depth |
| 1 | exec error: parameter 'boss_radius' already exists |
| 1 | exec error: 'Part' object has no attribute 'sweep_raft' |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'thickness' |
| 1 | exec error: Part.plate() got an unexpected keyword argument 'depth' |
| 1 | exec error: 'Part' object has no attribute 'fit' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'profile_radius' |
| 1 | exec error: 'Part' object has no attribute 'circle' |
| 1 | SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<unknown>, line 18) |
| 1 | exec error: 'Part' object has no attribute 'rectangular_ribbed_support' |
| 1 | exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'profile_type' |
| 1 | exec error: Parameters.add() got an unexpected keyword argument 'role' |
| 1 | exec error: Part.boss() got an unexpected keyword argument 'position' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'profile' |
| 1 | exec error: Part.linear_pattern() got an unexpected keyword argument 'offset' |
| 1 | exec error: Part.offset() got an unexpected keyword argument 'offset_distance' |
| 1 | exec error: 'list' object has no attribute 'strip' |
| 1 | exec error: 'Part' object has no attribute 'lobed_lug_profile' |
| 1 | exec error: name 'pocket' is not defined |
| 1 | exec error: 'FeatureHandle' object has no attribute 'boss_edges' |
| 1 | exec error: 'upper_radius' |
| 1 | exec error: 'Part' object has no attribute 'profile_trapezoid' |
| 1 | exec error: 'Part' object has no attribute 'face_cut_on_profile' |
| 1 | exec error: length must resolve to a number, got 'width * 0.72' |
| 1 | exec error: Part.plate() got an unexpected keyword argument 'radius' |
| 1 | exec error: Part.shelled_cover_plate() got an unexpected keyword argument 'hole_pattern' |
| 1 | exec error: 'Part' object has no attribute 'shelled_hole_plate' |
| 1 | exec error: 'lobe_radius' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path_thickness' |
| 1 | exec error: 'Part' object has no attribute 'hole_role' |
| 1 | exec error: 'Part' object has no attribute 'mounting_block_plate' |
| 1 | exec error: 'Part' object has no attribute 'footprint' |
| 1 | exec error: parameter 'thickness' already exists |
| 1 | exec error: parameter 'lower_width' already exists |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 11) |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'profile_height' |
| 1 | exec error: 'Part' object has no attribute 'face_from_profile' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'bottom_inner_edges' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path' |
| 1 | exec error: Part.sphere() got an unexpected keyword argument 'clip_radius' |
| 1 | exec error: Part.sketch_polygon() got an unexpected keyword argument 'profile' |
| 1 | exec error: 'Part' object has no attribute 'plate_milspec' |
| 1 | exec error: 'Part' object has no attribute 'lobe' |
| 1 | exec error: 'Part' object has no attribute 'plate_pattern' |
| 1 | exec error: 'Part' object has no attribute 'profile_for_sweep' |
| 1 | exec error: 'Part' object has no attribute 'boolean_difference' |
| 1 | exec error: 'Part' object has no attribute 'profile_on_plate' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'edgescatches' |
| 1 | exec error: 'Part' object has no attribute 'sweep_on_face' |
| 1 | exec error: topology reference 'loft_001:top_face:b95a905e855a' did not resolve any face |
| 1 | exec error: 'Part' object has no attribute 'boolean_lug' |
| 1 | exec error: Part.__init__() got an unexpected keyword argument 'min_width' |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'diameter' |
| 1 | exec error: 'Part' object has no attribute 'rectangular_rib' |
| 1 | exec error: Part.cylinder() got an unexpected keyword argument 'height_semia_axis' |
| 1 | exec error: Part.boss() got an unexpected keyword argument 'boss_height' |
| 1 | exec error: 'Part' object has no attribute 'pocketed_service_plate' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 10) |
| 1 | exec error: 'Part' object has no attribute 'sweep_sphere_path' |
| 1 | exec error: unsupported operand type(s) for *: 'ParameterRef' and 'ParameterRef' |
| 1 | exec error: Part.profile_cut_on_face() missing 1 required keyword-only argument: 'depth' |
| 1 | exec error: 'Part' object has no attribute 'mounting_block' |
| 1 | exec error: 'relief_height' |
| 1 | exec error: name 'move' is not defined |
| 1 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'pocket_positions' |
| 1 | exec error: 'inner_width' |
| 1 | exec error: 'Part' object has no attribute 'profile_cosmos' |
| 1 | exec error: 'Part' object has no attribute 'path' |
| 1 | SyntaxError: unmatched ']' (<unknown>, line 20) |
| 1 | exec error: topology reference 'hole_001:top_face:9014e73e3f7b' did not resolve any face |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 33) |
| 1 | exec error: parameter 'major_radius' already exists |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'thread_segments' |
| 1 | exec error: 'Part' object has no attribute 'sketch_on_top' |
| 1 | exec error: mirror: axis must be 'X', 'Y', or 'Z' |

### text / B

Scoreable=1192; target-present=2500; missing-target=0; kernel-crashes=0; export-but-unscoreable=103; gate/geometry flag-mismatch cases=0; CD>1000 scored cases=5.
First failure stages: `{"exec_ok_failure": 776, "post_export_geometry_failure": 103, "scoreable": 1192, "step_export_ok_failure": 53, "syntax_ok_failure": 376}`.
Geometry-run gate counts: `{"build_ok": 1348, "exec_ok": 1348, "solid_valid": 1348, "step_export_ok": 1295, "syntax_ok": 2124}`.
Native gate runtime seconds=570.902; native geometry Python=3.11.11. Geometry runtime is not separately measured by this script; no wall-time estimate is invented.
Retained last-attempt geometry resume messages: `[]`. The last log is not a complete independent retry history.

| Count | Exact error |
| ---: | --- |
| 309 | SyntaxError: unmatched ']' (<unknown>, line 1) |
| 103 | point cloud sampling failed on generated part |
| 59 | exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face |
| 53 | STEP export error: OCCT build failed |
| 52 | exec error: topology reference 'revolve_001:top_face:d95ca6795e31' did not resolve any face |
| 45 | exec error: 'lower_radius' |
| 43 | exec error: Part.plate() got an unexpected keyword argument 'length' |
| 35 | exec error: points[] must be a 2D sequence |
| 35 | exec error: Part.circular_pattern() got an unexpected keyword argument 'radius' |
| 34 | exec error: mirror: plane must be 'YZ', 'XZ', or 'XY' |
| 29 | exec error: topology reference 'join_002:top_face:323af5d41048' did not resolve any face |
| 28 | exec error: target must be a FeatureHandle |
| 26 | exec error: Part.loft() got an unexpected keyword argument 'target' |
| 22 | exec error: 'Part' object has no attribute 'join' |
| 18 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'profile' |
| 12 | exec error: Part.boolean_cut() got an unexpected keyword argument 'depth' |
| 11 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'positions' |
| 11 | SyntaxError: invalid syntax (<unknown>, line 1) |
| 11 | exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float' |
| 10 | exec error: 'Part' object has no attribute 'rectangular_slot' |
| 10 | exec error: topology reference 'sweep_tube_001:top_face:b2f164f681f5' did not resolve any face |
| 10 | exec error: topology reference 'loft_001:top_face:b95a905e855a' did not resolve any face |
| 9 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 10) |
| 9 | exec error: 'Part' object has no attribute 'box_constraint' |
| 8 | exec error: 'Part' object has no attribute 'extrude_solid' |
| 8 | exec error: Part.wedge() got an unexpected keyword argument 'width' |
| 7 | SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 1) |
| 7 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'radius' |
| 7 | exec error: topology reference 'pocket_001:top_outer_edges:0501fba53d98' did not resolve any edge_set |
| 7 | exec error: Part.sketch_on_face() got an unexpected keyword argument 'face' |
| 6 | exec error: Part.hole_pattern() got an unexpected keyword argument 'position' |
| 6 | exec error: 'Part' object has no attribute 'extrude_profile' |
| 6 | exec error: extrude_on_face cut requires depth |
| 6 | exec error: Part.shell() got an unexpected keyword argument 'layers' |
| 6 | exec error: 'FeatureHandle' object has no attribute 'height' |
| 6 | exec error: 'Part' object has no attribute 'move' |
| 6 | exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'jaw_spacing' |
| 6 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 16) |
| 5 | SyntaxError: unterminated string literal (detected at line 18) (<unknown>, line 18) |
| 5 | exec error: Part.sketch_on_face() got an unexpected keyword argument 'offset' |
| 4 | exec error: 'Part' object has no attribute 'box_on_face' |
| 4 | exec error: name 'math' is not defined |
| 4 | exec error: 'Part' object has no attribute 'sketch_on_plate' |
| 4 | SyntaxError: '(' was never closed (<unknown>, line 14) |
| 4 | exec error: 'FeatureHandle' object has no attribute 'top_center' |
| 4 | exec error: 'Part' object has no attribute 'extrude_on_profile' |
| 4 | exec error: 'Part' object has no attribute 'threaded_bearing_hole' |
| 4 | exec error: Part.bossed_plate() got an unexpected keyword argument 'chamfer_distance' |
| 4 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'min_length' |
| 4 | exec error: 'Part' object has no attribute 'profile_offset' |
| 3 | exec error: 'Part' object has no attribute 'bosses' |
| 3 | exec error: 'Part' object has no attribute 'lobed_profile_on_polygon' |
| 3 | exec error: target must be a TopologyReference from a FeatureHandle |
| 3 | exec error: 'Part' object has no attribute 'threaded_bearing_plate_on_face' |
| 3 | exec error: topology reference 'pocket_001:top_face:6bc5ae6c80c5' did not resolve any face |
| 3 | exec error: FeatureHandle.top_face() got an unexpected keyword argument 'name' |
| 3 | exec error: 'upper_width' |
| 3 | exec error: Part.hole_pattern() got an unexpected keyword argument 'offsets' |
| 3 | exec error: Part.plate() got an unexpected keyword argument 'depth' |
| 3 | exec error: Part.loft() got an unexpected keyword argument 'profile' |
| 3 | SyntaxError: '[' was never closed (<unknown>, line 18) |
| 3 | exec error: name 'pocket_2' is not defined |
| 3 | exec error: bad operand type for unary -: 'ParameterRef' |
| 2 | exec error: depth must be positive, got -2.24 |
| 2 | exec error: loft requires at least two profile features |
| 2 | exec error: Part.revolve() got an unexpected keyword argument 'radius' |
| 2 | SyntaxError: '[' was never closed (<unknown>, line 10) |
| 2 | exec error: Part.box() got an unexpected keyword argument 'target' |
| 2 | exec error: Part.sweep_tube() got an unexpected keyword argument 'profile_name' |
| 2 | SyntaxError: unterminated string literal (detected at line 17) (<unknown>, line 17) |
| 2 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_reference' |
| 2 | exec error: 'FeatureHandle' object has no attribute 'top_edges' |
| 2 | exec error: 'Part' object has no attribute 'threaded_bearing_hole_on_plate' |
| 2 | exec error: 'Part' object has no attribute 'rectangular_slot_on_face' |
| 2 | exec error: 'Part' object has no attribute 'profile_sketch' |
| 2 | exec error: Part.revolve() got an unexpected keyword argument 'axis' |
| 2 | exec error: topology reference 'extrude_001:top_face:b9ec9b032ae6' did not resolve any face |
| 2 | exec error: 'Part' object has no attribute 'section' |
| 2 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'thread_type' |
| 2 | exec error: Part.box() got an unexpected keyword argument 'thickness' |
| 2 | exec error: float() argument must be a string or a real number, not 'list' |
| 2 | exec error: 'Part' object has no attribute 'threaded_bearing_on_face' |
| 2 | exec error: 'FeatureHandle' object has no attribute 'min_corner' |
| 2 | exec error: 'Part' object has no attribute 'bolt_hole_pattern' |
| 2 | exec error: Part.extrude() got an unexpected keyword argument 'thickness' |
| 2 | exec error: 'Part' object has no attribute 'threaded_bearing_contract' |
| 1 | exec error: 'Part' object has no attribute 'rectangular_pocket_profile' |
| 1 | exec error: 'Part' object has no attribute 'text_callout_on_face' |
| 1 | exec error: 'Part' object has no attribute 'box_set' |
| 1 | SyntaxError: invalid syntax (<unknown>, line 2) |
| 1 | exec error: 'FeatureHandle' object has no attribute 'holes' |
| 1 | exec error: 'Part' object has no attribute 'loft_profiles' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 13) |
| 1 | exec error: Part.translate() got an unexpected keyword argument 'position' |
| 1 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'semantic_position' |
| 1 | exec error: 'Part' object has no attribute 'leaf_plate' |
| 1 | exec error: 'Part' object has no attribute 'offset_profile' |
| 1 | exec error: 'Part' object has no attribute 'boolean_join_matrix' |
| 1 | exec error: 'Part' object has no attribute 'fin' |
| 1 | exec error: hole pattern positions must be 2D or 3D sequences |
| 1 | exec error: 'Part' object has no attribute 'rectangular_pocket_on_face' |
| 1 | SyntaxError: positional argument follows keyword argument (<unknown>, line 24) |
| 1 | exec error: Part.rotate() got an unexpected keyword argument 'angle' |
| 1 | exec error: 'Part' object has no attribute 'sweep_bracket' |
| 1 | exec error: hole depth must be a number or 'through' |
| 1 | SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<unknown>, line 8) |
| 1 | exec error: 'FeatureHandle' object has no attribute 'minimums' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'height' |
| 1 | exec error: 'TopologyReference' object has no attribute 'size' |
| 1 | exec error: Part.shell() got an unexpected keyword argument 'offset' |
| 1 | exec error: 'Part' object has no attribute 'offset_on_face' |
| 1 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'position' |
| 1 | exec error: 'upper_profile' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'reverse' |
| 1 | exec error: 'flange_profile' |
| 1 | exec error: Part.extrude() got an unexpected keyword argument 'length' |
| 1 | exec error: Part.sketch_on_face() got an unexpected keyword argument 'closed' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 14) |
| 1 | exec error: Part.loft() got an unexpected keyword argument 'upper_radius' |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 7) |
| 1 | exec error: 'Part' object has no attribute 'text_callout' |
| 1 | exec error: thickness must resolve to a number, got 'thick' |
| 1 | SyntaxError: unterminated string literal (detected at line 25) (<unknown>, line 25) |
| 1 | exec error: 'Part' object has no attribute 'profile_list' |
| 1 | exec error: 'length' |
| 1 | SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 2) |
| 1 | exec error: Part.extrude() got an unexpected keyword argument 'layer_count' |
| 1 | exec error: Part.shell() got an unexpected keyword argument 'profile' |
| 1 | exec error: could not convert string to float: 'center' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'profile_type' |
| 1 | exec error: 'Part' object has no attribute 'threaded_bearing_plate' |
| 1 | exec error: Part.pin_cluster() got an unexpected keyword argument 'row_width' |
| 1 | exec error: 'Part' object has no attribute 'fpdf_print' |
| 1 | exec error: Part.shell() got an unexpected keyword argument 'profiles' |
| 1 | SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 3) |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'direction' |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'target' |
| 1 | SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<unknown>, line 12) |
| 1 | exec error: 'Part' object has no attribute 'face_on_face' |
| 1 | exec error: Part.__init__() got an unexpected keyword argument 'version' |
| 1 | exec error: 'width' |
| 1 | exec error: Part.loft() got an unexpected keyword argument 'targets' |
| 1 | exec error: 'Part' object has no attribute 'placement' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 23) |
| 1 | exec error: topology reference 'face_add_002:top_outer_edges:01fed540c0f6' did not resolve any edge_set |
| 1 | exec error: 'Part' object has no attribute 'rectangular_slot_profile' |
| 1 | exec error: 'Part' object has no attribute 'profile_extrude' |
| 1 | SyntaxError: positional argument follows keyword argument (<unknown>, line 15) |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_profile' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_edge' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 16) |
| 1 | exec error: 'Part' object has no attribute 'morph_profile' |
| 1 | exec error: topology reference 'cut_001:top_face:e6c86e3e481d' did not resolve any face |
| 1 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'offset' |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'thickness' |
| 1 | SyntaxError: positional argument follows keyword argument (<unknown>, line 16) |
| 1 | exec error: 'function' object has no attribute 'top_center' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'min' |
| 1 | exec error: 'Part' object has no attribute 'threaded_profile_on_face' |
| 1 | SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<unknown>, line 23) |
| 1 | exec error: depth must resolve to a number, got '-through' |
| 1 | exec error: 'Part' object has no attribute 'hole_on_face' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'profile_radius' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 18) |
| 1 | exec error: 'Part' object has no attribute 'offset_face_profile' |
| 1 | exec error: 'Part' object has no attribute 'face' |
| 1 | SyntaxError: unterminated string literal (detected at line 16) (<unknown>, line 16) |
| 1 | exec error: 'Part' object has no attribute 'profile_rectangle' |
| 1 | exec error: offset must be a 3D sequence |
| 1 | exec error: Parameters.add() got an unexpected keyword argument 'category' |
| 1 | exec error: Part.clipped_offset_stock() got an unexpected keyword argument 'offset_axis' |
| 1 | exec error: topology reference 'hole_001:top_face:9014e73e3f7b' did not resolve any face |
| 1 | exec error: 'Part' object has no attribute 'lofted_solid' |
| 1 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'height' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 25) |
| 1 | exec error: Parameters.add() got an unexpected keyword argument 'step' |
| 1 | exec error: 'Part' object has no attribute 'loft_profile' |
| 1 | exec error: 'Part' object has no attribute 'loft_on_face' |
| 1 | exec error: Part.cylinder() got an unexpected keyword argument 'thickness' |
| 1 | exec error: 'upper_flange_width' |
| 1 | exec error: thickness must resolve to a number, got 'through' |
| 1 | exec error: 'Part' object has no attribute 'box_shadow' |
| 1 | exec error: 'Part' object has no attribute 'threaded_bearing_contractor' |

### image / A

Scoreable=1283; target-present=2500; missing-target=0; kernel-crashes=0; export-but-unscoreable=38; gate/geometry flag-mismatch cases=0; CD>1000 scored cases=1.
First failure stages: `{"exec_ok_failure": 1074, "post_export_geometry_failure": 38, "scoreable": 1283, "step_export_ok_failure": 31, "syntax_ok_failure": 74}`.
Geometry-run gate counts: `{"build_ok": 1352, "exec_ok": 1352, "solid_valid": 1352, "step_export_ok": 1321, "syntax_ok": 2426}`.
Native gate runtime seconds=166.269; native geometry Python=3.11.11. Geometry runtime is not separately measured by this script; no wall-time estimate is invented.
Retained last-attempt geometry resume messages: `[]`. The last log is not a complete independent retry history.

| Count | Exact error |
| ---: | --- |
| 165 | exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face |
| 91 | exec error: target must be a TopologyReference from a FeatureHandle |
| 54 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'position' |
| 47 | exec error: parameter 'path_length' already exists |
| 40 | exec error: Part.loft() got an unexpected keyword argument 'target' |
| 38 | point cloud sampling failed on generated part |
| 37 | exec error: 'width' |
| 36 | exec error: Part.plate() got an unexpected keyword argument 'length' |
| 34 | exec error: 'Part' object has no attribute 'profile_on_plate' |
| 31 | SyntaxError: invalid syntax (<unknown>, line 1) |
| 31 | STEP export error: OCCT build failed |
| 26 | exec error: mirror: plane must be 'YZ', 'XZ', or 'XY' |
| 25 | exec error: Part.extrude() got an unexpected keyword argument 'operation' |
| 23 | exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float' |
| 23 | exec error: Part.circular_pattern() got an unexpected keyword argument 'radius' |
| 22 | exec error: offset must be a 3D sequence |
| 20 | exec error: 'Part' object has no attribute 'lofted_flange' |
| 19 | exec error: Part.box() got an unexpected keyword argument 'thickness' |
| 19 | exec error: Part.circular_pattern() got an unexpected keyword argument 'offset' |
| 18 | exec error: 'Part' object has no attribute 'sweep_profile' |
| 14 | exec error: 'Part' object has no attribute 'slot_pattern' |
| 13 | exec error: 'Part' object has no attribute 'bosses_plate' |
| 13 | exec error: Part.hole_pattern() missing 1 required keyword-only argument: 'target' |
| 12 | exec error: parameter 'height' already exists |
| 9 | exec error: target must be a FeatureHandle |
| 8 | exec error: Part.cone() got an unexpected keyword argument 'height_top' |
| 8 | exec error: 'Part' object has no attribute 'face_add' |
| 7 | exec error: Part.cylinder() got an unexpected keyword argument 'length' |
| 7 | exec error: 'Part' object has no attribute 'profile_cut' |
| 7 | exec error: topology reference 'revolve_001:top_face:d95ca6795e31' did not resolve any face |
| 7 | exec error: Part.boolean_cut() got an unexpected keyword argument 'depth' |
| 7 | exec error: bad operand type for unary -: 'ParameterRef' |
| 7 | exec error: Part.torus() got an unexpected keyword argument 'radius' |
| 6 | exec error: Part.boolean_join() got an unexpected keyword argument 'operation' |
| 6 | exec error: extrude_on_face join/add requires height |
| 5 | SyntaxError: unmatched ']' (<unknown>, line 1) |
| 5 | exec error: 'Part' object has no attribute 'rectangular_solid_slot' |
| 5 | exec error: Part.standoff_array_plate() got an unexpected keyword argument 'hole_offset_x' |
| 5 | exec error: 'Part' object has no attribute 'offset_hole_pattern' |
| 5 | exec error: 'height' |
| 5 | exec error: 'Part' object has no attribute 'face_add_on_profile' |
| 5 | exec error: Part.hole_pattern() got an unexpected keyword argument 'offset' |
| 5 | exec error: 'Part' object has no attribute 'lofted_transition_bracket' |
| 4 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'offset' |
| 4 | exec error: unsupported operand type(s) for /: 'ParameterRef' and 'float' |
| 4 | exec error: 'Part' object has no attribute 'sweep_pipe_bracket' |
| 4 | exec error: Part.wedge() got an unexpected keyword argument 'thickness' |
| 4 | SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 1) |
| 4 | exec error: 'relief_height' |
| 4 | exec error: 'Part' object has no attribute 'boss_profile' |
| 4 | exec error: hole depth must be a number or 'through' |
| 3 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_from' |
| 3 | exec error: 'Part' object has no attribute 'boss_on_plate' |
| 3 | exec error: 'Part' object has no attribute 'profile_set' |
| 3 | exec error: 'Part' object has no attribute 'bosses_on_plate' |
| 3 | exec error: 'Part' object has no attribute 'threaded_bearing_plate' |
| 3 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_x' |
| 3 | exec error: topology reference 'join_002:top_face:323af5d41048' did not resolve any face |
| 3 | exec error: Part.hole_pattern() got an unexpected keyword argument 'position' |
| 3 | exec error: 'Part' object has no attribute 'path' |
| 3 | exec error: 'list' object has no attribute 'strip' |
| 3 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 25) |
| 3 | exec error: 'Part' object has no attribute 'footing' |
| 3 | exec error: 'Part' object has no attribute 'rectangular_cutout' |
| 3 | exec error: 'Part' object has no attribute 'foot' |
| 3 | exec error: 'threaded_width' |
| 3 | exec error: 'FeatureHandle' object has no attribute 'top_profile' |
| 3 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 21) |
| 2 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_guides' |
| 2 | exec error: 'Part' object has no attribute 'face_by_profile' |
| 2 | exec error: 'path_width' |
| 2 | exec error: Part.cylinder() got an unexpected keyword argument 'offset' |
| 2 | exec error: Part.plate() got an unexpected keyword argument 'hole_radius' |
| 2 | exec error: object of type 'float' has no len() |
| 2 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'offset' |
| 2 | SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<unknown>, line 12) |
| 2 | exec error: 'Part' object has no attribute 'crescent_lug_profile' |
| 2 | exec error: 'Part' object has no attribute 'extrude_on_profile' |
| 2 | exec error: 'Part' object has no attribute 'rectangular_slot' |
| 2 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 22) |
| 2 | exec error: Part.standoff_array_plate() got an unexpected keyword argument 'standoff_count' |
| 2 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'thread_radius' |
| 2 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'include' |
| 2 | exec error: 'upper_slot_depth' |
| 2 | exec error: 'Part' object has no attribute 'footprint' |
| 2 | exec error: 'Part' object has no attribute 'loft_on_face' |
| 2 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'thread_frequency' |
| 2 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 18) |
| 2 | exec error: hole pattern positions must be 2D or 3D sequences |
| 2 | exec error: 'Part' object has no attribute 'rib_profile' |
| 2 | exec error: 'FeatureHandle' object has no attribute 'top_edges' |
| 2 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'profile' |
| 2 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'positions' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 17) |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 34) |
| 1 | exec error: 'Part' object has no attribute 'foot_plate' |
| 1 | exec error: Part.standoff_array_plate() got an unexpected keyword argument 'standoff_positions' |
| 1 | exec error: 'upper_slot_length' |
| 1 | exec error: parameter 'fillet_radius' already exists |
| 1 | exec error: 'Part' object has no attribute 'slot_profile' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 27) |
| 1 | exec error: 'Part' object has no attribute 'loft_transition' |
| 1 | exec error: 'upper_lug_width' |
| 1 | exec error: Part.shell() got an unexpected keyword argument 'face_to_remove' |
| 1 | exec error: Part.boolean_cut() got an unexpected keyword argument 'offset' |
| 1 | exec error: 'Part' object has no attribute 'bosses' |
| 1 | exec error: 'Part' object has no attribute 'spherical_flange' |
| 1 | SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<unknown>, line 30) |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'depth_direction' |
| 1 | exec error: Part.shelled_cover_plate() got an unexpected keyword argument 'hole_offsets' |
| 1 | exec error: 'upper_length' |
| 1 | exec error: 'upper_height' |
| 1 | exec error: Part.torus() got an unexpected keyword argument 'radius_inner' |
| 1 | exec error: Part.shell() got an unexpected keyword argument 'inner_box' |
| 1 | exec error: direction must be 'inward' or 'outward' |
| 1 | exec error: 'Part' object has no attribute 'lofted_plate' |
| 1 | SyntaxError: invalid syntax. Maybe you meant '==' or ':=' instead of '='? (<unknown>, line 19) |
| 1 | exec error: 'Part' object has no attribute 'profile_half_profile' |
| 1 | exec error: Part.profile_cut_on_face() missing 1 required keyword-only argument: 'depth' |
| 1 | exec error: 'Part' object has no attribute 'bolt_hole_pattern' |
| 1 | exec error: Part.shell() got an unexpected keyword argument 'covers' |
| 1 | SyntaxError: invalid decimal literal (<unknown>, line 1) |
| 1 | exec error: 'Part' object has no attribute 'extrude_face_cut' |
| 1 | exec error: Part.torus() got an unexpected keyword argument 'radius_out' |
| 1 | SyntaxError: invalid syntax (<unknown>, line 34) |
| 1 | exec error: Parameters.add() got an unexpected keyword argument 'category' |
| 1 | exec error: 'Part' object has no attribute 'line' |
| 1 | exec error: 'Part' object has no attribute 'profile_cross_section' |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'target' |
| 1 | exec error: 'Part' object has no attribute 'face_extrude' |
| 1 | exec error: Part.shell() got an unexpected keyword argument 'shell_seed' |
| 1 | exec error: 'Part' object has no attribute 'ribbed_clamp' |
| 1 | exec error: topology reference 'join_001:top_outer_edges:95c539c404ed' did not resolve any edge_set |
| 1 | exec error: 'Part' object has no attribute 'hole_on_face' |
| 1 | exec error: Part.torus() got an unexpected keyword argument 'inner_radius' |
| 1 | exec error: 'Part' object has no attribute 'boolean_add' |
| 1 | exec error: 'Part' object has no attribute 'footpring' |
| 1 | exec error: Part.standoff_array_plate() got an unexpected keyword argument 'offset' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 42) |
| 1 | exec error: 'Part' object has no attribute 'booss_plate' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 18) |
| 1 | exec error: 'Part' object has no attribute 'clamp_jaw' |
| 1 | exec error: 'Part' object has no attribute 'lofted_plate_on_face' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 20) |
| 1 | exec error: Part.standoff_array_plate() got an unexpected keyword argument 'standoff_spacing' |
| 1 | exec error: 'Part' object has no attribute 'loft_on_plate' |
| 1 | exec error: 'Part' object has no attribute 'hole_pattern_on_face' |
| 1 | exec error: row_step must be a 3D sequence |
| 1 | exec error: 'Part' object has no attribute 'face_on_face' |
| 1 | exec error: topology reference 'loft_001:top_face:b95a905e855a' did not resolve any face |
| 1 | exec error: keyword argument repeated: path_length (<candidate>, line 24) |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path_offset_x' |
| 1 | SyntaxError: invalid syntax. Maybe you meant '==' or ':=' instead of '='? (<unknown>, line 10) |
| 1 | exec error: 'thickness' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'thickness' |
| 1 | exec error: 'Part' object has no attribute 'face_sketch' |
| 1 | exec error: points[] must be a 2D sequence |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 23) |
| 1 | exec error: 'length' |
| 1 | exec error: Part.circular_pattern() got an unexpected keyword argument 'center' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path_midaxis_tilt' |
| 1 | SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<unknown>, line 15) |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path' |
| 1 | exec error: 'boss_radius' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top' |
| 1 | exec error: 'bolt_pad_length' |
| 1 | exec error: 'Part' object has no attribute 'lobed_gasket_profile' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'translate' |
| 1 | exec error: Part.pin_cluster() got an unexpected keyword argument 'radial_offset' |
| 1 | exec error: Part.sweep_tube() missing 1 required keyword-only argument: 'path_mid_length' |
| 1 | exec error: topology reference 'intersect_002:top_face:35b57a3f0eb3' did not resolve any face |
| 1 | SyntaxError: invalid syntax (<unknown>, line 2) |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_edge' |
| 1 | exec error: 'Part' object has no attribute 'clipped_offset_sphere' |
| 1 | exec error: Part.__init__() got an unexpected keyword argument 'version' |
| 1 | exec error: Part.pin_cluster() got an unexpected keyword argument 'offset' |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 42) |
| 1 | exec error: 'Part' object has no attribute 'boss_plate' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 10) |
| 1 | exec error: Part.hole_pattern() got an unexpected keyword argument 'count' |
| 1 | exec error: Part.cylinder() got an unexpected keyword argument 'profile_offset' |
| 1 | SyntaxError: unterminated string literal (detected at line 36) (<unknown>, line 36) |
| 1 | exec error: 'Part' object has no attribute 'profile_on_sweep' |
| 1 | exec error: Part.shell() got an unexpected keyword argument 'seed' |
| 1 | exec error: 'Part' object has no attribute 'face_extrude_on_profile' |
| 1 | exec error: Part.loft() got an unexpected keyword argument 'profile' |
| 1 | exec error: 'Part' object has no attribute 'face_on_top' |
| 1 | exec error: Part.chamfer() got an unexpected keyword argument 'length' |
| 1 | exec error: 'Part' object has no attribute 'boss_on_top' |
| 1 | SyntaxError: unterminated string literal (detected at line 16) (<unknown>, line 16) |
| 1 | exec error: Parameters.add() got an unexpected keyword argument 'enum' |
| 1 | exec error: 'Part' object has no attribute 'face_mount_on_plate' |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'min_depth' |
| 1 | SyntaxError: unterminated string literal (detected at line 43) (<unknown>, line 43) |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 24) |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'thread_height' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 40) |
| 1 | exec error: 'lower_lug_width' |
| 1 | exec error: loft requires at least two profile features |
| 1 | exec error: Part.threaded_hole_on_face() missing 1 required keyword-only argument: 'depth' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 19) |
| 1 | exec error: Part.cone() got an unexpected keyword argument 'view_radius' |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path_offset_y' |
| 1 | exec error: workplane_polygon requires at least 3 points |
| 1 | exec error: Part.sweep_tube() got an unexpected keyword argument 'path_width' |
| 1 | exec error: 'Part' object has no attribute 'profile_cross' |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_frequency' |

### image / B

Scoreable=1264; target-present=2500; missing-target=0; kernel-crashes=0; export-but-unscoreable=73; gate/geometry flag-mismatch cases=0; CD>1000 scored cases=21.
First failure stages: `{"exec_ok_failure": 698, "post_export_geometry_failure": 73, "scoreable": 1264, "step_export_ok_failure": 84, "syntax_ok_failure": 381}`.
Geometry-run gate counts: `{"build_ok": 1421, "exec_ok": 1421, "solid_valid": 1421, "step_export_ok": 1337, "syntax_ok": 2119}`.
Native gate runtime seconds=1000.127; native geometry Python=3.11.11. Geometry runtime is not separately measured by this script; no wall-time estimate is invented.
Retained last-attempt geometry resume messages: `[]`. The last log is not a complete independent retry history.

| Count | Exact error |
| ---: | --- |
| 350 | SyntaxError: unmatched ']' (<unknown>, line 1) |
| 84 | STEP export error: OCCT build failed |
| 73 | point cloud sampling failed on generated part |
| 42 | exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face |
| 34 | exec error: 'Part' object has no attribute 'rectangular_slot' |
| 33 | exec error: target must be a FeatureHandle |
| 31 | exec error: Part.circular_pattern() got an unexpected keyword argument 'radius' |
| 29 | exec error: Part.shell() got an unexpected keyword argument 'layers' |
| 25 | exec error: Part.sketch_on_face() got an unexpected keyword argument 'face' |
| 22 | exec error: topology reference 'revolve_001:top_face:d95ca6795e31' did not resolve any face |
| 21 | exec error: target must be a TopologyReference from a FeatureHandle |
| 18 | exec error: Part.extrude_on_face() got an unexpected keyword argument 'profile' |
| 18 | exec error: mirror: plane must be 'YZ', 'XZ', or 'XY' |
| 16 | exec error: Part.box() got an unexpected keyword argument 'thickness' |
| 16 | exec error: points[] must be a 2D sequence |
| 15 | exec error: 'Part' object has no attribute 'move' |
| 14 | exec error: 'Part' object has no attribute 'rectangular_slot_on_face' |
| 13 | exec error: topology reference 'pocket_001:top_face:6bc5ae6c80c5' did not resolve any face |
| 12 | exec error: Part.loft() got an unexpected keyword argument 'upper_radius' |
| 11 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'min_length' |
| 11 | exec error: 'Part' object has no attribute 'profile_offset' |
| 10 | exec error: Part.boolean_cut() got an unexpected keyword argument 'depth' |
| 10 | exec error: Part.plate() got an unexpected keyword argument 'length' |
| 9 | exec error: 'Part' object has no attribute 'bosses' |
| 9 | exec error: 'Part' object has no attribute 'box_constraint' |
| 9 | exec error: 'Part' object has no attribute 'boss_profile' |
| 9 | exec error: topology reference 'join_002:top_face:323af5d41048' did not resolve any face |
| 9 | exec error: bad operand type for unary -: 'ParameterRef' |
| 8 | exec error: Part.hole_pattern() got an unexpected keyword argument 'position' |
| 8 | exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float' |
| 8 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'positions' |
| 8 | exec error: 'Part' object has no attribute 'threaded_bearing_hole' |
| 8 | exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'jaw_spacing' |
| 8 | exec error: Part.pin_cluster() missing 2 required keyword-only arguments: 'row_count' and 'row_step' |
| 7 | SyntaxError: invalid syntax (<unknown>, line 1) |
| 7 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'radius' |
| 6 | SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 1) |
| 6 | exec error: depth must be positive, got 0.0 |
| 6 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 16) |
| 6 | exec error: Part.rectangular_pocket() got an unexpected keyword argument 'height' |
| 6 | exec error: 'Part' object has no attribute 'box_on_face' |
| 6 | exec error: 'lower_radius' |
| 5 | exec error: 'Part' object has no attribute 'profile_revolve' |
| 5 | exec error: Part.sketch_on_face() got an unexpected keyword argument 'closed' |
| 5 | exec error: '<' not supported between instances of 'ParameterRef' and 'ParameterRef' |
| 5 | exec error: hole pattern positions must be 2D or 3D sequences |
| 5 | exec error: 'Part' object has no attribute 'extrude_profile' |
| 4 | exec error: Part.pin_cluster() got an unexpected keyword argument 'row_width' |
| 4 | exec error: offset must be a 3D sequence |
| 4 | exec error: 'Part' object has no attribute 'top_face' |
| 4 | exec error: Part.loft() got an unexpected keyword argument 'target' |
| 4 | exec error: hole depth must be a number or 'through' |
| 3 | exec error: unsupported operand type(s) for /: 'ParameterRef' and 'float' |
| 3 | exec error: 'Part' object has no attribute 'section_profile' |
| 3 | exec error: 'Part' object has no attribute 'extrude_solid' |
| 3 | exec error: depth must be positive, got -2.24 |
| 3 | exec error: 'Part' object has no attribute 'threaded_bearing_contract' |
| 3 | exec error: 'list' object has no attribute 'strip' |
| 3 | exec error: Part.sketch_polygon() got an unexpected keyword argument 'vertices' |
| 3 | exec error: extrude_on_face cut requires depth |
| 3 | exec error: Part.loft() got an unexpected keyword argument 'profile' |
| 3 | exec error: 'FeatureHandle' object has no attribute 'edge_breaks' |
| 2 | exec error: loft requires at least two profile features |
| 2 | exec error: 'Part' object has no attribute 'offset_profile' |
| 2 | exec error: Part.rotate() got an unexpected keyword argument 'angle' |
| 2 | SyntaxError: '[' was never closed (<unknown>, line 9) |
| 2 | exec error: 'Part' object has no attribute 'text' |
| 2 | exec error: 'Part' object has no attribute 'lobed_profile' |
| 2 | exec error: 'Part' object has no attribute 'box_shell' |
| 2 | exec error: 'FeatureHandle' object has no attribute 'top_outer_profile' |
| 2 | exec error: Part.bossed_plate() missing 2 required keyword-only arguments: 'hole_radius' and 'hole_positions' |
| 2 | exec error: 'Part' object has no attribute 'loft_profile' |
| 2 | SyntaxError: '[' was never closed (<unknown>, line 11) |
| 2 | exec error: 'Part' object has no attribute 'hole' |
| 2 | exec error: unsupported operand type(s) for +: 'ParameterRef' and 'float' |
| 2 | exec error: 'Part' object has no attribute 'profile_sketch' |
| 1 | exec error: depth must resolve to a number, got 'through' |
| 1 | exec error: Part.extrude() got an unexpected keyword argument 'operation' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 12) |
| 1 | exec error: Part.cylinder() got an unexpected keyword argument 'length' |
| 1 | exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'operation' |
| 1 | exec error: Part.wedge() got an unexpected keyword argument 'width' |
| 1 | exec error: unsupported sketch_on_face profile [[-33.28, -17.74], [33.28, -17.74], [33.28, 17.74], [18.94, 17.74], [18.94, -8.9], [-18.94, -8.9], [-18.94, 17.74], [-33.28, 17.74]] |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 21) |
| 1 | exec error: topology reference 'cut_001:top_face:e6c86e3e481d' did not resolve any face |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_left' |
| 1 | exec error: unsupported sketch_on_face profile [[-35.32, -22.74], [35.32, -22.74], [35.32, 22.74], [21.21, 22.74], [21.21, -13.06], [-21.21, -13.06], [-21.21, 22.74], [-35.32, 22.74]] |
| 1 | exec error: 'upper_width' |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 9) |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'target' |
| 1 | exec error: Part.hole_pattern() got an unexpected keyword argument 'offsets' |
| 1 | exec error: unsupported sketch_on_face profile [[[-10.05, -19.92], [10.05, -19.92], [10.05, 19.92], [-10.05, 19.92]], [[-10.05, -19.92], [-8.66, -15.536], [-8.66, -10.152], [-10.05, -6.768]]] |
| 1 | exec error: 'Part' object has no attribute 'shift' |
| 1 | exec error: 'Part' object has no attribute 'thickness' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_profile' |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_left_corner' |
| 1 | exec error: 'Part' object has no attribute 'callout_on_face' |
| 1 | exec error: 'Part' object has no attribute 'profile_polygon' |
| 1 | exec error: 'Part' object has no attribute 'gamma_profile' |
| 1 | exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'width' |
| 1 | exec error: Part.shell() got an unexpected keyword argument 'profiles' |
| 1 | SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 20) |
| 1 | exec error: 'Part' object has no attribute 'hole_on_face' |
| 1 | exec error: 'profile_name' |
| 1 | exec error: topology reference 'cut_002:top_face:d7e817b6f02b' did not resolve any face |
| 1 | exec error: parameter 'thickness' already exists |
| 1 | exec error: Part.boolean_cut() got an unexpected keyword argument 'position' |
| 1 | exec error: Part.extrude() got an unexpected keyword argument 'length' |
| 1 | exec error: 'Part' object has no attribute 'profile_on_face' |
| 1 | exec error: FeatureHandle.edges() got an unexpected keyword argument 'outer_boss_edges' |
| 1 | exec error: unsupported sketch_on_face profile [[-31.38, -19.12], [31.38, -19.12], [31.38, 19.12], [18.11, 19.12], [18.11, -10.04], [-18.11, -10.04], [-18.11, 19.12], [-31.38, 19.12]] |
| 1 | exec error: 'Part' object has no attribute 'extra_fillet' |
| 1 | exec error: 'Part' object has no attribute 'rectangular_fillet' |
| 1 | exec error: 'Part' object has no attribute 'lobed_profile_on_sketch' |
| 1 | exec error: 'Part' object has no attribute 'threaded_profile_on_face' |
| 1 | exec error: 'Part' object has no attribute 'threaded_bearing_contracted' |
| 1 | exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'offset_profile' |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 8) |
| 1 | exec error: 'Part' object has no attribute 'profile_plane' |
| 1 | exec error: Part.linear_pattern() missing 1 required keyword-only argument: 'step' |
| 1 | exec error: 'Part' object has no attribute 'hole_profile' |
| 1 | exec error: Part.extrude() got an unexpected keyword argument 'thickness' |
| 1 | SyntaxError: '[' was never closed (<unknown>, line 15) |
| 1 | exec error: 'Part' object has no attribute 'mount_block' |
| 1 | exec error: Part.cylinder() got an unexpected keyword argument 'min_radius' |
| 1 | exec error: 'Part' object has no attribute 'sheetmetal_process' |
| 1 | exec error: 'path_width' |
| 1 | exec error: depth must be positive, got -9.66 |
| 1 | exec error: 'Part' object has no attribute 'extrude_seeded' |
| 1 | exec error: Part.rail_mount_plate() got an unexpected keyword argument 'boss_radius' |
| 1 | exec error: topology reference 'pocket_001:top_outer_edges:0501fba53d98' did not resolve any edge_set |
| 1 | exec error: 'pocket_height' |
| 1 | exec error: 'Part' object has no attribute 'lobed_profile_on_polygon' |
| 1 | exec error: unsupported sketch_on_face profile [[-33.78, -19.26], [33.78, -19.26], [33.78, 19.26], [20.19, 19.26], [20.19, -10.51], [-20.19, -10.51], [-20.19, 19.26], [-33.78, 19.26]] |
| 1 | SyntaxError: '(' was never closed (<unknown>, line 27) |
| 1 | SyntaxError: unterminated string literal (detected at line 15) (<unknown>, line 15) |
| 1 | exec error: 'Part' object has no attribute 'mechanical_bag' |
| 1 | exec error: name 'hole' is not defined |
| 1 | exec error: Part.rail_mount_plate() got an unexpected keyword argument 'hole_offsets' |
| 1 | exec error: 'Part' object has no attribute 'face_extrude_cut' |
| 1 | exec error: 'Part' object has no attribute 'profile_join_on_face' |
| 1 | exec error: Part.cylinder() got an unexpected keyword argument 'width' |
| 1 | exec error: unsupported sketch_on_face profile [[-39.09, -17.01], [39.09, -17.01], [39.09, 17.01], [-39.09, 17.01]] |
| 1 | exec error: unsupported sketch_on_face profile [[-38.12, -22.74], [38.12, -22.74], [38.12, 22.74], [22.11, 22.74], [22.11, -12.52], [-22.11, -12.52], [-22.11, 22.74], [-38.12, 22.74]] |
| 1 | exec error: name 'pocket_2' is not defined |
| 1 | exec error: extrude_on_face join/add requires height |
| 1 | exec error: 'FeatureHandle' object has no attribute 'top_edges' |
| 1 | exec error: unsupported sketch_on_face profile [[-36.38, -16.17], [36.38, -16.17], [36.38, 16.17], [22.1, 16.17], [22.1, -9.2], [-22.1, -9.2], [-22.1, 16.17], [-36.38, 16.17]] |
| 1 | exec error: Part.shell() got an unexpected keyword argument 'depth' |
| 1 | exec error: 'hole_radius' |
| 1 | exec error: Part.revolve() got an unexpected keyword argument 'radius' |
| 1 | exec error: 'Part' object has no attribute 'profile_mirror' |
| 1 | exec error: 'width' |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'minimum_length' |
| 1 | exec error: unsupported sketch_on_face profile [[-38.12, -19.12], [38.12, -19.12], [38.12, 19.12], [22.11, 19.12], [22.11, -10.3], [-22.11, -10.3], [-22.11, 19.12], [-38.12, 19.12]] |
| 1 | exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_reference' |
| 1 | exec error: 'Part' object has no attribute 'rectangular_pocket_profile' |
| 1 | exec error: 'Part' object has no attribute 'loft_on_face' |

## Full Paths And SHA256

WSL source checkout: `__RUN_SOURCE_ROOT__`; Windows source checkout: `__DEV_ROOT__`; evidence package: `__EVIDENCE_SOURCE_ROOT__\04`. Release records retain historical Git/dirty-tree/source inventories; hashes, not an assumed clean commit, identify the executed sources. Do not substitute another checkout when publishing.

Training implementation: `src/training_25k/cag_exposure_policy.py`, B-only continuation `cag_exposure_policy_b_only.py`, isolated Stage4b `cag_stage4b_execution.py`, training packer `cag_stage4b_packing_v1.py`; inference `cag_exposure_inference.py`. Exact source hashes are bound through `dependencies` and the immutable training/prediction records, not newly inferred from file names.

| Artifact | Path | SHA256 |
| --- | --- | --- |
| gate_registration | `__EVIDENCE_SOURCE_ROOT__/04/execution/exposure_gate_completed_20261021.json` | `e630f98493f0e06a1798c5b7ab7f8c2e9ebe575865017f11214a22386450d279` |
| prediction_registration | `__EVIDENCE_SOURCE_ROOT__/04/execution/exposure_prediction_B_and_paired_completed_20261021.json` | `ad6b18e5a6c9d744b204f9bac67a35611bc5441e063a2a76607da4e846ac845d` |
| final_registrar | `__EVIDENCE_SOURCE_ROOT__/04/execution/register_exposure_final_results.py` | `4c288072db51e5534750a890f768b66f338758da81d47e4284ba482a05ec5a3a` |
| final_tests | `__EVIDENCE_SOURCE_ROOT__/04/execution/exposure_final_audit_tests_20261022.json` | `9afcadd33dd69b7bc463d8cfaf1b2436e1406e150142b37a0cb9449519cb52f7` |
| prior_metric_helpers | `__DEV_ROOT__/src/training_25k/cag_summarize_b0_b2_fullstack_eval.py` | `cc7c5ccc753e99765a69b211c6f48bdae377d9781b9aa85c54b1c05edcf3f898` |
| evaluate_execution.ps1 | `__DEV_ROOT__/src/scripts/evaluate_execution.ps1` | `92b40099e790e97e55a7c5624dc082691318078561e6a20648cce863fb61d63d` |
| evaluate_execution.py | `__RUN_SOURCE_ROOT__/evaluate_execution.py` | `cf6d1ee0bf3cd029ba34c8b5fcef95724aab11b18397b40fb222bc5cf8b9ca32` |
| evaluate_geometry_nbest.ps1 | `__DEV_ROOT__/src/scripts/evaluate_geometry_nbest.ps1` | `20af50d489d431b20af3f86911621acbfe38a8f24acc967834fb3ff9b913427a` |
| evaluate_geometry_nbest.py | `__RUN_SOURCE_ROOT__/evaluate_geometry_nbest.py` | `4da5f7fe12c4207f85be4fe2dfb30dda357f70c0c8ef55e9912fb1c6ff480e8f` |
| A/step/geometry_nbest_rows.jsonl | `__DEV_ROOT__/scratch/geom_r04_step_A/geometry_nbest_rows.jsonl` | `77256a1a66a492e2d09396efb0692e51855593e1a65fc5ed1a8cfaa46888eab0` |
| A/step/cli.log | `__DEV_ROOT__/scratch/geom_r04_step_A/cli.log` | `92dd209b33a066debc276c734e74990c01b27cb6cfcef790a95768d6cb99ff90` |
| A/step/geometry_input | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_A/geom_input_step.jsonl` | `fe03807fb515d2dd78afe81b772df229d08b8fd27ceec36ee14613011013a3bb` |
| A/step/prediction | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_A/test_code_step.jsonl` | `4d0aacc5020cd9c159f50c2d91ff8683b6bb0b2889b0f9f180ce93382619354b` |
| A/step/staged_input | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_step_A/input.jsonl` | `fe03807fb515d2dd78afe81b772df229d08b8fd27ceec36ee14613011013a3bb` |
| A/step/staged_evaluator | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_step_A/evaluate_geometry_nbest.py` | `4da5f7fe12c4207f85be4fe2dfb30dda357f70c0c8ef55e9912fb1c6ff480e8f` |
| A/step/gate/cli.log | `__DEV_ROOT__/scratch/exec_r04_step_A/cli.log` | `df9b4185da6c36cfb3ff9b268d8bf5a3675fc73f140a80a1893969c3efc61bc7` |
| A/step/gate/execution_rows.jsonl | `__DEV_ROOT__/scratch/exec_r04_step_A/execution_rows.jsonl` | `3b195ae46b16ccb01f37cbd6c85db0ea19043bb349d6c1b5d0443d9d382932ad` |
| A/step/gate/execution_summary.json | `__DEV_ROOT__/scratch/exec_r04_step_A/execution_summary.json` | `e95091fb581461faec4c158fe918f31d4e624169483de092bf8ccf2155fb8564` |
| A/point/geometry_nbest_rows.jsonl | `__DEV_ROOT__/scratch/geom_r04_point_A/geometry_nbest_rows.jsonl` | `10def9224f515325a60a26269d4de60d74fb41d3cb03dcc046dc5ccc048cb052` |
| A/point/cli.log | `__DEV_ROOT__/scratch/geom_r04_point_A/cli.log` | `11cbfc40fe046200462f53d47f033dfa5490461ba8cb80fdd08368e9e525a621` |
| A/point/geometry_input | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_A/geom_input_point.jsonl` | `d5c282cc0dc64414b0ec3b682033c8c2f8471d6c04b5a97a2504a8a278a8fc80` |
| A/point/prediction | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_A/test_code_point.jsonl` | `8f120d97ea32db147479e8041de66dc66e6b1d4b7109c04c1672e0bbdd1825dc` |
| A/point/staged_input | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_point_A/input.jsonl` | `d5c282cc0dc64414b0ec3b682033c8c2f8471d6c04b5a97a2504a8a278a8fc80` |
| A/point/staged_evaluator | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_point_A/evaluate_geometry_nbest.py` | `4da5f7fe12c4207f85be4fe2dfb30dda357f70c0c8ef55e9912fb1c6ff480e8f` |
| A/point/gate/cli.log | `__DEV_ROOT__/scratch/exec_r04_point_A/cli.log` | `5bac0b1b0f5e0d6009d58bb013032bbf5ebd6d091050b6217523940268b5bc39` |
| A/point/gate/execution_rows.jsonl | `__DEV_ROOT__/scratch/exec_r04_point_A/execution_rows.jsonl` | `7c1873d58cf9048e4a29300e5399247c8049411b590c7504edbf9176bdfee93f` |
| A/point/gate/execution_summary.json | `__DEV_ROOT__/scratch/exec_r04_point_A/execution_summary.json` | `8f7a27bbf5e4c202ee4c52a8c37b036eba87218757b35308d27cfa88f3f548ba` |
| A/text/geometry_nbest_rows.jsonl | `__DEV_ROOT__/scratch/geom_r04_text_A/geometry_nbest_rows.jsonl` | `79a1cc9746e489c21d288aee4d19a8416dc470a3b8a05728cffa5fee2e52b530` |
| A/text/cli.log | `__DEV_ROOT__/scratch/geom_r04_text_A/cli.log` | `742c4699c01e7ed01ec1dd845e324863ad7776ecbdc322f8d33536279793f645` |
| A/text/geometry_input | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_A/geom_input_text.jsonl` | `926bd854352114ecc1bf9c05fa3236f30bc926beff75f523bd201608fe94e18a` |
| A/text/prediction | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_A/test_code_text.jsonl` | `451dda600e579d82d65c7f01e09256c6d2dc4b4d67fcac307f612338457968cc` |
| A/text/staged_input | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_text_A/input.jsonl` | `926bd854352114ecc1bf9c05fa3236f30bc926beff75f523bd201608fe94e18a` |
| A/text/staged_evaluator | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_text_A/evaluate_geometry_nbest.py` | `4da5f7fe12c4207f85be4fe2dfb30dda357f70c0c8ef55e9912fb1c6ff480e8f` |
| A/text/gate/cli.log | `__DEV_ROOT__/scratch/exec_r04_text_A/cli.log` | `55ff078e9cada6adb2dcbdb131f4374704f98616706a4ce06383c286df38d9f8` |
| A/text/gate/execution_rows.jsonl | `__DEV_ROOT__/scratch/exec_r04_text_A/execution_rows.jsonl` | `2a5e5169a8eadb00b4b6db3aaf66dddba64f5f7542035cbeef6ea1e7c4437f88` |
| A/text/gate/execution_summary.json | `__DEV_ROOT__/scratch/exec_r04_text_A/execution_summary.json` | `978eaad37cdb367a69e1b508aed7a0e991e11b68e0afbe57108626070bac1bf2` |
| A/image/geometry_nbest_rows.jsonl | `__DEV_ROOT__/scratch/geom_r04_image_A/geometry_nbest_rows.jsonl` | `4a1130b21c66491e6f3c6c87948b41320340d6986e2cc38ee064d1175026b8ae` |
| A/image/cli.log | `__DEV_ROOT__/scratch/geom_r04_image_A/cli.log` | `e6e6a7bd695706c43e53e344309740cfda6352667ddce3b58597190240d66752` |
| A/image/geometry_input | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_A/geom_input_image.jsonl` | `51347a9e8d69c9fa1452d73d0ee1cbd45e3a5da5b6fc7bf9c26fda7fd5eecc9e` |
| A/image/prediction | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_A/test_code_image.jsonl` | `1c9b50eba659ab569c66b7dd4e0d0ea319d5627c587a9773e677bfd84e802ad8` |
| A/image/staged_input | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_image_A/input.jsonl` | `51347a9e8d69c9fa1452d73d0ee1cbd45e3a5da5b6fc7bf9c26fda7fd5eecc9e` |
| A/image/staged_evaluator | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_image_A/evaluate_geometry_nbest.py` | `4da5f7fe12c4207f85be4fe2dfb30dda357f70c0c8ef55e9912fb1c6ff480e8f` |
| A/image/gate/cli.log | `__DEV_ROOT__/scratch/exec_r04_image_A/cli.log` | `4cd807326658cb79b3b1e5dd691a356daa772fd0c749201101a0134c1e8860e7` |
| A/image/gate/execution_rows.jsonl | `__DEV_ROOT__/scratch/exec_r04_image_A/execution_rows.jsonl` | `4b354fa29af7a3f8609494be61e09d4f83eab85a68c5f34bcabe8ca816a2a27e` |
| A/image/gate/execution_summary.json | `__DEV_ROOT__/scratch/exec_r04_image_A/execution_summary.json` | `eb285ea4910babbad7905508fddd1fd249d35ab0713204cce9c5a2489c7e2dad` |
| B/step/geometry_nbest_rows.jsonl | `__DEV_ROOT__/scratch/geom_r04_step_B/geometry_nbest_rows.jsonl` | `d8ca8b089b752f1816f5757d6f7631af4e5348c8f6113d521aff5ed603ac4400` |
| B/step/cli.log | `__DEV_ROOT__/scratch/geom_r04_step_B/cli.log` | `3699a7e8475ede238c40d2c035242396bc3fa71b91b22355571dfffd6aa6e60d` |
| B/step/geometry_input | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_B/geom_input_step.jsonl` | `fd79e5c6a3dbbda86ad5cb7a1e104530c27b2ac5eacdf63ea737d863f87560f8` |
| B/step/prediction | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_B/test_code_step.jsonl` | `164e65c40d8d214f6c6c3d96210772818247167f29fe3053853c05253cc87adb` |
| B/step/staged_input | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_step_B/input.jsonl` | `fd79e5c6a3dbbda86ad5cb7a1e104530c27b2ac5eacdf63ea737d863f87560f8` |
| B/step/staged_evaluator | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_step_B/evaluate_geometry_nbest.py` | `4da5f7fe12c4207f85be4fe2dfb30dda357f70c0c8ef55e9912fb1c6ff480e8f` |
| B/step/gate/cli.log | `__DEV_ROOT__/scratch/exec_r04_step_B/cli.log` | `5c7472f8bf402f42c88e27ce14670d868155060f8a874a7c2476118f52685287` |
| B/step/gate/execution_rows.jsonl | `__DEV_ROOT__/scratch/exec_r04_step_B/execution_rows.jsonl` | `126e2f176d00459042f4307d6636c85c377afcf09e6eef385aad90eb29ae686c` |
| B/step/gate/execution_summary.json | `__DEV_ROOT__/scratch/exec_r04_step_B/execution_summary.json` | `9cd0d7426f86361fe820a8abcc558903f269ce93cd93a90b490d6f72cbcaffa1` |
| B/point/geometry_nbest_rows.jsonl | `__DEV_ROOT__/scratch/geom_r04_point_B/geometry_nbest_rows.jsonl` | `d1b47219d5ef4408b07e07848e10a5dc5dbd2b45b2863278c953a2c1304d14dd` |
| B/point/cli.log | `__DEV_ROOT__/scratch/geom_r04_point_B/cli.log` | `1651daf2c94ab4a8de21a2ee03351aacd2fb58c2abeb98895464f40db7883189` |
| B/point/geometry_input | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_B/geom_input_point.jsonl` | `b3d6d1be0df11269b04aa0a06d61321d8ea738a0facaf5f3453db3fa9780f5a7` |
| B/point/prediction | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_B/test_code_point.jsonl` | `9cbded2fdf1c5536be39f99ef6492370bedd0843b516c993d061b1b7994c8280` |
| B/point/staged_input | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_point_B/input.jsonl` | `b3d6d1be0df11269b04aa0a06d61321d8ea738a0facaf5f3453db3fa9780f5a7` |
| B/point/staged_evaluator | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_point_B/evaluate_geometry_nbest.py` | `4da5f7fe12c4207f85be4fe2dfb30dda357f70c0c8ef55e9912fb1c6ff480e8f` |
| B/point/gate/cli.log | `__DEV_ROOT__/scratch/exec_r04_point_B/cli.log` | `7f2631fdcca93b8d4b18b9b995949099a6e8b943eefa291a39a623c20fd12e8b` |
| B/point/gate/execution_rows.jsonl | `__DEV_ROOT__/scratch/exec_r04_point_B/execution_rows.jsonl` | `394885c4ba4f0703385fd02eb573c0193a4b4752c982430a4782380ca173251c` |
| B/point/gate/execution_summary.json | `__DEV_ROOT__/scratch/exec_r04_point_B/execution_summary.json` | `575b9da5da96a83011d61c0b7381317ee496cb5e006a135c3ec4507bc777b74f` |
| B/text/geometry_nbest_rows.jsonl | `__DEV_ROOT__/scratch/geom_r04_text_B/geometry_nbest_rows.jsonl` | `c642b0721af49f7a315e1c8fd0fbe0ca9e2d81a9de5f272cfac00acffbe6e03c` |
| B/text/cli.log | `__DEV_ROOT__/scratch/geom_r04_text_B/cli.log` | `f3c745da971bc026478e1e65cfd24e5932d7f003579b6babb9f38adebf5fbbf3` |
| B/text/geometry_input | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_B/geom_input_text.jsonl` | `f6c7163e6ff44da629a9cf0a0f2fd2b802d5bb733bff8ecd14bf7e9a1571fbb1` |
| B/text/prediction | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_B/test_code_text.jsonl` | `004c16ac06424e28e808550b67a6e21e8734903ddef4b984da854a260c797ed1` |
| B/text/staged_input | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_text_B/input.jsonl` | `f6c7163e6ff44da629a9cf0a0f2fd2b802d5bb733bff8ecd14bf7e9a1571fbb1` |
| B/text/staged_evaluator | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_text_B/evaluate_geometry_nbest.py` | `4da5f7fe12c4207f85be4fe2dfb30dda357f70c0c8ef55e9912fb1c6ff480e8f` |
| B/text/gate/cli.log | `__DEV_ROOT__/scratch/exec_r04_text_B/cli.log` | `bcfd46fd67a700d82ef24c753411f77c7e763f1214bd05c2a2774d9fe57f22de` |
| B/text/gate/execution_rows.jsonl | `__DEV_ROOT__/scratch/exec_r04_text_B/execution_rows.jsonl` | `f4c0d2d9537142c57396a347cf33d7c967a64d4a92b4f635c6ec761869e12575` |
| B/text/gate/execution_summary.json | `__DEV_ROOT__/scratch/exec_r04_text_B/execution_summary.json` | `d8c33e5d76c1d776ba554bbcec5528edd8c4a60d5e38d9f34e2140fd933c41c1` |
| B/image/geometry_nbest_rows.jsonl | `__DEV_ROOT__/scratch/geom_r04_image_B/geometry_nbest_rows.jsonl` | `60021ac7b0d380215a76ee1d6ee1d83d1745dc2524bb0f2dc2e1966430500f8d` |
| B/image/cli.log | `__DEV_ROOT__/scratch/geom_r04_image_B/cli.log` | `74bc12ce9104e093f8b64aed71758ae37089445b031b01414b7ecafc2b25690c` |
| B/image/geometry_input | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_B/geom_input_image.jsonl` | `ac127a251f598a36840ffbd50f4f2b8b16a0a3a2f5aef464e9427488eddb4f09` |
| B/image/prediction | `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_B/test_code_image.jsonl` | `f2bb9082003f796ac55d233f59a8b2a6cceb01ea9a00c97ea3756275d6b17f90` |
| B/image/staged_input | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_image_B/input.jsonl` | `ac127a251f598a36840ffbd50f4f2b8b16a0a3a2f5aef464e9427488eddb4f09` |
| B/image/staged_evaluator | `/mnt/c/tmp/MIRAGE/geometry_nbest/geom_r04_image_B/evaluate_geometry_nbest.py` | `4da5f7fe12c4207f85be4fe2dfb30dda357f70c0c8ef55e9912fb1c6ff480e8f` |
| B/image/gate/cli.log | `__DEV_ROOT__/scratch/exec_r04_image_B/cli.log` | `63537a3d3159b6c337a14d2218fb98ee43f63fd627e182706fef07641cb00688` |
| B/image/gate/execution_rows.jsonl | `__DEV_ROOT__/scratch/exec_r04_image_B/execution_rows.jsonl` | `12ee81b1a4304b198b357895b41531d69cb4e36f1a84696e97c9bc3d84211f2a` |
| B/image/gate/execution_summary.json | `__DEV_ROOT__/scratch/exec_r04_image_B/execution_summary.json` | `6e7c6eea4483b17699f0da39161451e5dbdf9dc8c032e884f7bd0028d69da2a1` |
| paired_cases/step | `__EVIDENCE_SOURCE_ROOT__/04/result/paired_cases_step.jsonl` | `40a438a07202381e214e13dbc648d2a99cc10c17bcc7f37295df84900a469455` |
| paired_cases/point | `__EVIDENCE_SOURCE_ROOT__/04/result/paired_cases_point.jsonl` | `75a7496a3927ab0b591e4174d88791770cb590485616847926d317dc7ab07cd2` |
| paired_cases/text | `__EVIDENCE_SOURCE_ROOT__/04/result/paired_cases_text.jsonl` | `276fa626dbf8da45e3d045766f049f7efd1c675802357a76d53e428006e9238e` |
| paired_cases/image | `__EVIDENCE_SOURCE_ROOT__/04/result/paired_cases_image.jsonl` | `6593e7c67bb932d472f74828e28fd040a20b672c1b92ecf8d543399054a56f27` |

## Claim Boundaries

This result answers whether the predeclared exposure policies change the modality profile in this single matched diagnostic. It cannot establish seed-level robustness, equivalence, broad external generalization, or that shared architecture alone caused the observed differences. Report every modality and retain syntax/export/scoreable/fidelity trade-offs even when Build increases. Whole-prompt test cropping differed between arms; this is a measured downstream behavior under the same decoding rule, not an arm-specific test-time packing change. The Stage4b post-freeze target-preserving training amendment and its timing remain disclosed in records10-16; it is not a test-time target-aware procedure.

Original frozen62-file package remains unchanged. Both trained arm trees and both prediction trees were verified against their prior read-only inventories before and after this audit. Native evaluator sources and every previously registered gate artifact remain unchanged. No additional seed, new training, weight selection or evaluation retry was performed by this registrar.
