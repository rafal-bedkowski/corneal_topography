# Dataset description: Keratoconus detection (Kaggle)

Source: https://www.kaggle.com/datasets/elmehdi12/keratoconus-detection/data
Provided by the Product Owner from the Kaggle dataset page. The text below is the dataset description as shown on that page, followed by page metadata.

## Page metadata

- Title: Keratoconus detection
- Subtitle: Keratoconus detection which each corneal have 7 maps
- Usability: 7.50
- License: "Other (specified in description)" — the description text does not name a specific license, and the Product Owner confirmed the page contains no license information; treat redistribution rights as unknown
- Expected update frequency: Never
- Tags: Image, Computer Vision, Eyes and Vision, Image Classification
- Version: 1 (50.47 MB), 4011 files

## Description

### Train Validation set (each has 7 corneal maps)

1. 150 NOR
2. 150 KCN
3. 123 Suspect

### Test set (each has 7 corneal maps)

1. 50 NOR
2. 50 KCN
3. 50 Suspect

### Datasets and pre-processing

The protocol of the study (0094/2020) was approved by the Institutional Review Board of Federal University of São Paulo - UNIFESP/EPM as coordinator center and Hospital de Olhos-CRO, Guarulhos, as side center. Corresponding data use agreements were signed among parties to use the data. The study was conducted in accordance with ethical standards in the declaration of Helsinki and its later amendments. If required, respective informed consent was obtained from participants and the data was de-identified in Brazil before any further processing.

Three corneal specialists (including RMH) conducted vision tests and ophthalmic examinations under standard conditions and collected corneal images using Scheimpflug imaging systems (Pentacam, Oculus Optikgeräte GmbH). There were three corneal trained specialists who performed eye classification. Disagreements were handled by favoring two versus one vote. The clinicians were instructed to grade each eye as normal, suspected KCN, or KCN.

Eyes were labeled as a KCN suspect based on standard criteria in earlier studies. More specifically, eyes were labeled as suspected KCN if corneal topography included atypical, localized steepening or an asymmetrical bowtie pattern. Eyes were labeled as suspected KCN if the keratometric curvature was greater than 47.00 D, oblique cylinder more than 1.50 D or central corneal thickness below 500 microns. Each eye of the patient was evaluated independently. Furthermore, raw data on the elevation maps, including Belin–Ambrosio Ectasia Display (BAD-D) indices, Progression Thickness Increase (PTI) represented by corneal thickness spatial profile (CTSP) and percentage of PTI. The Belin ABCD progression display was also examined. Eyes were labeled as suspected KCN if there was abnormal front elevation, high PTI, or abnormal BAD-D.

The development (training) dataset included corneal images collected using different Pentacam instruments with different settings (different color scale steps of the maps compared to the previous subset). All color scales were based on decimal scale grading using microns for corneal thickness, and elevation maps and diopters for axial/sagittal curvature maps.

An additional independent dataset, collected from a different clinic in Brazil, was also used to validate the proposed hybrid DL approach. A total of 204 eyes of 104 patients were normal (the group was represented as NOR), 215 eyes of 113 patients had KCN, and 123 eyes of 63 patients were suspected KCN (SUSPECT). The mean age (± SD) of the subjects in the normal, KCN, and suspected KCN were 33.4 (±10.1), 29.0 (±9.3), and 28.6 (±9.4) years, respectively. Images from 56 normal eyes and 58 eyes with KCN were collected from a Pentacam instrument with settings different from others.

The independent validation subset included 150 eyes of 85 patients collected from de Olhos-CRO private hospital (Guarulhos, SP, Brazil). This dataset included 50 normal eyes from 29 subjects, 50 KCN eyes from 31 patients, and 50 suspect KCN eyes from 25 patients. The mean age (± SD) of the subjects in the normal, KCN, and suspected KCN were 29.5 (±4.7), 26.3 (±6.8), and 29.1 (±5.3) years, respectively.

## Data Explorer (from the page)

- `Independent Test Set/` — "This file contains test images which is separated in 3 labels 'keratoconus', 'normal', 'suspect' which each corneal have 7 maps." Test set (each has 7 corneal maps): 50 NOR, 50 KCN, 50 Suspect.
- `Train_Validation sets/`
- Summary: 4011 files in total. This equals (423 train/validation eyes + 150 test eyes) × 7 maps.

## Notes

- The patient-level totals in the description (204 NOR, 215 KCN, 123 Suspect) describe the study cohort; the files contain 150 NOR / 150 KCN / 123 Suspect in Train_Validation and 50 / 50 / 50 in the Independent Test Set (verified in `dataset_review.md`).
- License is not stated anywhere on the page (confirmed by the Product Owner); see `dataset_review.md` for implications.
- File naming, map types, image format and sizes are documented in `dataset_review.md`.
