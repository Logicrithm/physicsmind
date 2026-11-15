**Problem statement**

A projectile is launched with an initial speed  

\[
v_0 = 30\ \text{m s}^{-1}
\]

at an angle  

\[
\theta = 45^{\circ}
\]

above the horizontal.  We are asked for its horizontal range (the distance it travels before it returns to the launch height).

**Assumptions**

1. Motion takes place near the Earth’s surface, so the gravitational acceleration is constant  

   \[
   g = 9.81\ \text{m s}^{-2}
   \]

2. Air resistance is neglected.
3. The launch and landing heights are the same (level ground).

**Symbols**

| Symbol | Meaning |
|--------|---------|
| \(v_0\) | initial speed (m s\(^{-1}\)) |
| \(\theta\) | launch angle measured from the horizontal (degrees or radians) |
| \(v_{0x}\) | horizontal component of \(v_0\) (m s\(^{-1}\)) |
| \(v_{0y}\) | vertical component of \(v_0\) (m s\(^{-1}\)) |
| \(t_f\) | total time of flight (s) |
| \(R\) | horizontal range (m) |
| \(g\) | magnitude of gravitational acceleration (m s\(^{-2}\)) |

**Step‑by‑step solution**

1. **Resolve the initial velocity into components**

   \[
   v_{0x}=v_0\cos\theta,\qquad 
   v_{0y}=v_0\sin\theta
   \]

   For \(\theta =45^{\circ}\),

   \[
   \cos45^{\circ} = \sin45^{\circ}= \frac{\sqrt{2}}{2}\approx0.7071
   \]

   Hence

   \[
   v_{0x}=30\,(0.7071)\approx 21.21\ \text{m s}^{-1}
   \]
   \[
   v_{0y}=30\,(0.7071)\approx 21.21\ \text{m s}^{-1}
   \]

2. **Find the time of flight**

   The vertical motion is described by  

   \[
   y(t)=v_{0y}t-\frac{1}{2}gt^{2}
   \]

   The projectile returns to the launch height when \(y=0\) (apart from the trivial solution \(t=0\)). Setting \(y=0\) and solving for the non‑zero root:

   \[
   0 = v_{0y}t-\frac{1}{2}gt^{2}
   \;\;\Longrightarrow\;\;
   t\bigl(v_{0y}-\tfrac{1}{2}gt\bigr)=0
   \]

   The non‑zero solution is  

   \[
   t_f = \frac{2v_{0y}}{g}
   \]

   Substituting the numbers:

   \[
   t_f = \frac{2(21.21\ \text{m s}^{-1})}{9.81\ \text{m s}^{-2}}
        \approx \frac{42.42}{9.81}
        \approx 4.33\ \text{s}
   \]

3. **Compute the horizontal range**

   Horizontal motion has constant velocity \(v_{0x}\) (no horizontal acceleration). The range is

   \[
   R = v_{0x}\,t_f
   \]

   \[
   R = (21.21\ \text{m s}^{-1})(4.33\ \text{s})
       \approx 91.7\ \text{m}
   \]

   (If you prefer the compact formula \(R = \dfrac{v_0^{2}\sin 2\theta}{g}\), note that \(\sin 2\theta = \sin 90^{\circ}=1\), giving the same result:
   \[
   R = \frac{30^{2}\times 1}{9.81}\approx 91.7\ \text{m}.
   \])

**Answer**

The horizontal range of the projectile is  

\[
\boxed{R \approx 9.2\times10^{1}\ \text{m}\; \text{(about 92 m)}}
\]

All quantities are expressed in SI units.
