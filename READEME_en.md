# Emotional Dialogue Dataset Collection Methodology

**Note: This project requires participants with strong self-learning abilities**

<p align="center">
📄 Technical Documentation • 🤖 Data Processing Tools • 🔍 Annotation Guidelines • 📊 Quality Assessment
</p>

~~阅读中文版 [Chinese](README.md)~~

## Project Updates
- 🔥 **Phase Two**: ```2025/1/15```: Total 400 data entries
- 🔥 **Phase One**: ```2025/1/6```: Complete annotation of 20 data entries per person

## Project Overview
This project aims to build a high-quality emotional dialogue dataset by collecting diverse conversational scenarios and implementing structured annotations to support emotional analysis research. The dataset contains rich emotional confrontation scenarios, with each dialogue undergoing careful preprocessing and annotation to ensure data quality and usability.

## Data Sources
| Source Type | Characteristics |
|-------------|----------------|
| Debates | Long dialogues, strong emotional confrontation, clear themes |
| Daily Arguments | Easy to collect, intense emotional confrontation, life-relevant |
| Seminars | Formal content, relevant to current situations, clear objectives |
| Movies/TV Series | Rich scenarios, various complex events |

## Data Processing Flow
### 1. Data Preprocessing
Supported transcription services:
- SenseVoice (requires local deployment)
- Feishu Minutes
- iFlytek Listen

**Processing Requirements:**
- SenseVoice: Manual speaker segmentation
- Feishu Minutes/iFlytek Listen: Manual review of transcribed text
- Clean irrelevant content (opening/closing credits, monologues, etc.)
- Export as plain text format (txt)

### 2. Annotation Process
#### 2.1 Dialogue Segmentation (Example)
```
Dialogue Group #2:
Speaker 2 00:26
Dialogue content...
Speaker 3 00:27
Response content...
```

#### 2.2 Automated Annotation (GLM-4-plus Output Example)
```json
{
  "sentence": "Dialogue text example",
  "Holder": "2",
  "Target": "topic",
  "Aspect": "specific aspect",
  "Opinion": "speaker's view",
  "Sentiment": "positive/negative/neutral",
  "Rationale": "annotation reason"
}
```

#### 2.3 Event Analysis (Example)
```json
{
  "1": {
    "events": [
      {
        "event": "Event description",
        "emotions": [
          {
            "state": "Emotional state",
            "reason": "Explanation"
          }
        ]
      }
    ]
  }
}
```

## Environment Requirements
- Python 3.10+
- GLM-4 API access
- Required Python packages:
  - pandas
  - json
  - os
  - re
  - zhipuai

## Delivery Milestones
### Phase One (January 6, 2025)
- Complete initial 20 data entries per person
- Familiarize with annotation method
- **Submit collected data by 14:00, January 6**

### Phase Two (January 15, 2025)
- Complete all emotional annotations
- Complete all event analyses
- Submit final dataset

## Quality Control
Annotation process requires checking:
- Speaker identification accuracy
- Segmentation context completeness
- Annotation consistency
- JSON format compliance

## Usage Instructions
1. Use git clone to download process.py and requirements.txt
2. Install dependencies using pip install -r requirements.txt ~~If installation fails, use pip install pandas, zhipuai~~
3. Modify your files and paths according to the code instructions
4. Click to run the code
5. Obtain the results
6. Package the results
