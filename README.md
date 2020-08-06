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
