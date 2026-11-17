**The three basic quantities**

| Symbol | Quantity | SI unit | What it tells you |
|--------|----------|---------|-------------------|
| $d$  | distance (or displacement) | metre (m) | how far something moves along a straight line |
| $t$  | time | second (s) | how long the motion lasts |
| $v$  | speed (or average speed) | metre per second (m s$^{-1}$) | how fast the object is moving, i.e. distance covered each second |

When an object moves **with a constant speed** (the same speed at every instant), the three quantities are linked by a simple linear relationship.  
The relationship can be written in three equivalent ways, each one solving for a different variable:

$$\boxed{v = \frac{d}{t}} \qquad
\boxed{d = v\,t} \qquad
\boxed{t = \frac{d}{v}}$$

These are just algebraic rearrangements of the same equation.  
Below we derive each form, explain the meaning, and work through a concrete example.

---

## 1. Speed from distance and time  

$$v = \frac{d}{t}$$

**Reasoning** – Speed tells you “how many metres are travelled each second”.  
If you know the total distance $d$ covered in a total time $t$, you divide the distance by the time to obtain the average speed.

### Example 1 (kilometres and hours, then convert to SI)

A car travels **150 km** in **3 h**.

1. Write the numbers with their units: $d = 150\;\text{km}$, $t = 3\;\text{h}$.
2. Compute the speed in the same units:  

   $$v = \frac{150\;\text{km}}{3\;\text{h}} = 50\;\text{km h}^{-1}.$$

3. If you want the SI value (m s$^{-1}$), convert:  

   $$1\;\text{km} = 10^{3}\;\text{m},\qquad
   1\;\text{h} = 3600\;\text{s}.$$

   $$v = 50\;\frac{10^{3}\;\text{m}}{3600\;\text{s}}
     \approx 13.9\;\text{m s}^{-1}.$$

So the car’s average speed is **50 km h$^{-1}$** (≈ 13.9 m s$^{-1}$).

---

## 2. Distance from speed and time  

$$d = v\,t$$

**Reasoning** – If you know how fast you are moving and for how long, multiply the two to get the total distance covered.

### Example 2 (SI units)

A cyclist rides at a steady **5 m s$^{-1}$** for **8 minutes**.

1. Convert the time to seconds:  

   $$8\;\text{min} = 8 \times 60\;\text{s} = 480\;\text{s}.$$

2. Multiply speed by time:  

   $$d = (5\;\text{m s}^{-1})(480\;\text{s}) = 2400\;\text{m}.$$

The cyclist travels **2.4 km**.

---

## 3. Time from distance and speed  

$$t = \frac{d}{v}$$

**Reasoning** – If you know how far you must go and how fast you can go, divide the distance by the speed to find how long it will take.

### Example 3 (mixed units)

A train must travel **300 km** and its average speed is **120 km h$^{-1}$**.

$$t = \frac{300\;\text{km}}{120\;\text{km h}^{-1}} = 2.5\;\text{h}.$$

In minutes: $2.5\;\text{h} \times 60\;\text{min h}^{-1}=150\;\text{min}$.

So the journey lasts **2 h 30 min**.

---

## 4. Important assumptions & pitfalls

1. **Uniform (constant) speed** – The formulas give the *average* speed when the speed changes during the trip. If the speed varies, you must integrate $v(t)$ over time, but for school‑level problems we usually assume a constant speed.
2. **Straight‑line motion** – Distance $d$ is taken as the length of the path along a straight line. If the path curves, the same formulas still apply as long as $d$ is the total path length.
3. **Consistent units** – Always keep the units the same when you plug numbers into the formulas. Mixing kilometres with metres or hours with seconds will give a wrong answer unless you convert first.

---

## 5. Quick “cheat‑sheet” for solving problems

| What you’re asked to find | What you need to know | Formula to use |
|---------------------------|-----------------------|----------------|
| Speed $v$               | Distance $d$ and time $t$ | $v = d/t$ |
| Distance $d$            | Speed $v$ and time $t$    | $d = v\,t$ |
| Time $t$                | Distance $d$ and speed $v$ | $t = d/v$ |

1. Write down the known quantities with their units.  
2. Convert everything to SI (m, s) **or** keep a consistent set of units (e.g., km and h).  
3. Insert the numbers into the appropriate formula.  
4. Perform the arithmetic, then attach the correct unit to the answer.  

---

### TL;DR

- **Speed** = distance ÷ time  $v = d/t$  
- **Distance** = speed × time  $d = v\,t$  
- **Time** = distance ÷ speed  $t = d/v$

These three equations are the cornerstone of everyday kinematics and are enough to solve most school‑level problems involving motion at constant speed. If you have a specific situation you’d like to work through, just let me know!
