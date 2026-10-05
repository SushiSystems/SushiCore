# Task 3 report: the brand data

## Files changed

- `sushicore/brand.py` (new): `K_TRANSPARENT`, `K_PALETTE`, `K_LOGO_PIXELS`.
- `tests/test_brand.py` (new): the seven tests from the plan, verbatim.
- Scratchpad, not in the repository: `trace.py`, `preview_22.png`, `grid_22.txt`.

## Result

- Grid: 22 columns by 20 rows (crop 616x532 px of the source, so 20 rows is the even rounding of 19).
- Palette measured from the PNG (median of each region, sampled every third pixel):
  - nori `#1a1c20` (7074 samples; the plan's starting value was `#1d1e20`)
  - rice `#f4f4f4` (14743)
  - amber `#f0a500` (6726)
  - green `#4caf50` (1686)
- Background: the PNG already has a real alpha channel (extrema 0 to 255), so nothing was flood-filled. The crop uses the bounding box of alpha above 40: (206, 254, 822, 786).
- Preview: `C:/Users/sushi/AppData/Local/Temp/claude/D--Projects-sushistack/43335f2f-2bdd-481b-a169-5cc2c051201f/scratchpad/preview_22.png` (16x nearest-neighbour, on a white backdrop, so rice and background look alike).

## Deviation from the plan's trace

Step 4 of the plan maps each pixel to the nearest palette colour by RGB distance. I ran that first. It turned the antialiased nori/rice blends on the thin left outline into green, and the outline disappeared in places. The final trace classifies instead:

- chroma above 45: `g` if the green channel beats red, else `a`;
- otherwise luminance below 190: `n`, else `r`.

The 190 threshold (150 lost the upper-left outline) keeps the thin left outline visible. The palette values in `brand.py` are still the measured ones. The classifier lives only in the scratch script.

## Comparison with the source

The preview reads as the same maki: a dark outline that is one cell thick on the left, top and bottom and four to five cells thick on the right; off-white rice around it; an amber disc whose flat lower-right edge sits on a green segment at its lower edge. Proportions match: amber spans columns 3 to 15 of 22 (source 3.6 to 15.3), the right nori band starts at column 18 (source 18.3). Left rice ring is about 2 cells where the source shows about 3, a cost of the 22-column limit.

## Commands

Step 2, before `brand.py` existed:

```
$ python -m pytest tests/test_brand.py -v
=================================== ERRORS ====================================
____________________ ERROR collecting tests/test_brand.py _____________________
ImportError while importing test module 'D:\Projects\sushicore\tests\test_brand.py'.
...
tests\test_brand.py:5: in <module>
    from sushicore.brand import K_LOGO_PIXELS, K_PALETTE, K_TRANSPARENT
E   ModuleNotFoundError: No module named 'sushicore.brand'
=========================== short test summary info ===========================
ERROR tests/test_brand.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.15s ===============================
```

Step 4, after:

```
$ python -m pytest tests/test_brand.py -v
collecting ... collected 7 items

tests/test_brand.py::test_every_row_has_the_same_width PASSED            [ 14%]
tests/test_brand.py::test_the_grid_has_an_even_number_of_rows PASSED     [ 28%]
tests/test_brand.py::test_the_grid_stays_small_enough_for_a_help_screen PASSED [ 42%]
tests/test_brand.py::test_the_grid_uses_only_palette_keys_and_the_transparent_key PASSED [ 57%]
tests/test_brand.py::test_every_palette_key_appears_in_the_grid PASSED   [ 71%]
tests/test_brand.py::test_palette_values_are_lowercase_hex_colours PASSED [ 85%]
tests/test_brand.py::test_the_palette_names_the_four_brand_keys PASSED   [100%]

============================== 7 passed in 0.03s ==============================
```

Syntax check:

```
$ python -m py_compile sushicore/brand.py tests/test_brand.py && echo compiled-ok
compiled-ok
```

## Final `K_LOGO_PIXELS`

```
"......nnnnnnnnnnn.....",
"...nnnrrrrrrrnnnnnn...",
"..nrrrrrrrrrrrrnnnn...",
".nrrrrrrrrrrrrrrnnnn..",
".nrrrrrraarrrrrrnnnnn.",
"nrrrrraaaaaarrrrrnnnn.",
"nrrrraaaaaaaarrrrnnnn.",
"nrrraaaaaaaaaarrrrnnnn",
"nrraaaaaaaaaaaarrrnnnn",
"nrraaaaaaaaaaaarrrnnnn",
"nrraaaaaaaaaaaaarrnnnn",
"nrrraaaaaaaaaaaarrnnnn",
"nrrraaaaaaaaaaarrrnnnn",
"nrrrraaagggggggrrrnnnn",
"nrrrraggggggggrrrrnnnn",
".nrrrrrrgggggrrrrrnnn.",
".nrrrrrrrrrrrrrrrnnn..",
"..nrrrrrrrrrrrrrnnn...",
"...nnrrrrrrrrrnnn.....",
".....nnnnnnnnn........",
```

## Not done

- I did not run the full suite, only `tests/test_brand.py`.
- I did not commit or touch `pyproject.toml`, `README.md`, `docs/README.md` or the changelog.
- The owner has not yet approved the look; that is the Wave 1 review.
