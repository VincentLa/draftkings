# DraftKings

A project to optimize lineups for Daily Fantasy Sports (DraftKings) starting with the NBA

## The Problem
We can frame this as a linear programming optimization problem. That is we are trying to pick 8 players let's call it:

- P_1 = (s1, p1)
- P_2 = (s2, p2)
- P_3 = (s3, p3)
- P_4 = (s4, p4)
- P_5 = (s5, p5)
- P_6 = (s6, p6)
- P_7 = (s7, p7)
- P_8 = (s8, p8)

where s = salary and p = points. and P_i is a player

We are trying to 

```
max(p1 + p2 + ... + p8)
```

subject to the constraint

```
s1 + ... + s8 = 50000
```

In addition, for basketball there are position constraints as well.

## Planned Work
1. Figure out how to (pref automatically) download DraftKings to get salary data. For now, we will manually download it by going to the context and exporting to CSV. Data is stored in [data/raw](./data/raw)
2. Figure out how to (pref automatically) download player stats per game. We really only need the stats that matter for draft kings, so Points, steals, blocks, assists, TO, 3 points made, and from there we can derive double-double, triple double, etc. After downloading the data, we'll need to use DraftKing's formula to convert to DraftKings Points.

As of 2020-08-05, the scoring rules are:
|Stat   | DraftKings Points   |
|---|---|
|Point   | +1  |
|Made 3 pt Shot   | +0.5  |
|Rebound   | +1.25  |
|Assist   | +1.5  |
|Steal   | +2  |
|Block   | +2  |
|Turnover   | -0.5  |
|Double-Double   | +1.5  |
|Triple-Double   | +3  |

3. Figure out how to (pref automatically) submit lineups to DraftKings.

## Potentially Useful Links
1. https://realpython.com/linear-programming-python/?fbclid=IwAR0WL4TShqaOHSJTcZFQZZ7QCfe1JmgAewu9V8RrvDOlPipQ7eAZ6FuohZA
2. https://github.com/jaebradley/draftkings_client
3. [Python Package for Scraping Basketball Reference for Box Scores](https://github.com/jaebradley/basketball_reference_web_scraper)
