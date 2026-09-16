# JalSetu — Water Bridge 💧

A smart, conjunctive canal-and-groundwater management system for the tail-end of the Lower Ganga Canal, Prayagraj — built for the 1M1B Green Skills & Applied AI for Climate Action internship.

**Live prototype:** file:///C:/Users/Asus/Downloads/jalsetu%20dashboard.html#problem
**Full portfolio deck:** [portfolio/JalSetu_Portfolio.pdf](portfolio/JalSetu_Portfolio.pdf)

## The Problem
When the Canal Runs Dry, the Aquifer Pays for It

Who's affected, and why it matters

> Tail-end smallholder farmers absorb yield loss and rising diesel-pumping costs every time the canal underdelivers.
> UP Irrigation Dept. engineers cannot manually police an ~8,183 km distributary network for equity.
> Groundwater is already the dominant irrigation source in UP — so a canal failure here is really a shared-aquifer failure.

## What I Discovered
The Missing Piece Wasn't Water — It Was Data

I went in expecting a water-scarcity problem. What I actually found was an information gap: two departments quietly running one shared hydrological system with no data passing between them. Fixing that data bridge matters more than any single new pump or pipe would.

## The AI-Enabled Solution
How AI is used
>A time-series LSTM model ingests canal discharge, groundwater depth, and weather data to output a Predicted Deficit Index — the core prediction driving every downstream decision.

Tools & technologies used
>Python
>HTML / CSS / JS
>LSTM (time-series forecasting)
>LoRaWAN + MQTT (IoT layer)

## Prototype
A Command Console You Can Actually Click Through


## Impact & Testing
Tested against five real scenarios

<img width="1834" height="392" alt="image" src="https://github.com/user-attachments/assets/81e29e8c-ed53-4787-8392-c2073e151080" />

Why that last row is the whole point:  a system watching only the canal would leave that gate shut, because the canal alone looks fine. JalSetu opens it anyway, reacting straight to the aquifer signal — which is really the entire reason this project exists.

## What's Next
From prototype to pilot

>Next Milestone
>>A Phase 1 pilot on 1–2 distressed minors in Prayagraj, feeding ~200 ha — instrumenting real gates with the same decision logic validated here.

## Repository Structure
JalSetu/
├── README.md
├── LICENSE
├── .gitignore
├── portfolio/
│   ├── JalSetu_Portfolio.pptx
│   └── JalSetu_Portfolio.pdf
├── prototype/
│   └── index.html                    ← JalSetu_Website.html (renamed)
└── hardware/
    ├── build-guide.md                 ← JalSetu_Mini_Build_Guide.md
    ├── jalsetu_mini.ino                ← JalSetu_Mini_Arduino_Code.ino
    └── wiring-diagram.svg             ← JalSetu_Wiring_Diagram.svg

## Author
Krish — Rajkiya Engineering College, Banda
