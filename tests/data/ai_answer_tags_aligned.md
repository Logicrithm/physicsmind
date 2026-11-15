**Deriving the projectile‑range formula**  

\[
R=\frac{u^{2}\,\sin (2\theta)}{g}
\]

where  

* \(R\) = horizontal distance (range) travelled before the projectile returns to the launch height, **metre (m)**  
* \(u\) = magnitude of the initial launch speed, **metre per second (m s⁻¹)**  
* \(\theta\) = launch angle measured from the horizontal, **radian (rad)** (the formula works for any angle, but \(\theta\) is usually given in degrees; just convert to rad when using trigonometric functions)  
* \(g\) = magnitude of the constant acceleration due to gravity, **metre per second squared (m s⁻²)** (≈ 9.81 m s⁻² near Earth’s surface)  

---

### 1. State the assumptions

1. **Uniform gravity** – the only force acting after launch is the weight \(mg\); \(g\) is constant and points vertically downward.  
2. **No air resistance** – the projectile moves only under gravity.  
3. **Flat ground** – the launch point and the landing point are at the same vertical height.  
4. **Rigid body, point mass** – the size of the projectile does not affect its trajectory.  

These are the standard “ideal projectile” conditions taught in high‑school physics.

---

### 2. Resolve the initial velocity into components

The launch speed \(u\) makes an angle \(\theta\) with the horizontal.

\[
\begin{aligned}
u_x &= u\cos\theta \qquad\text{(horizontal component, m s⁻¹)}\\[4pt]
u_y &= u\sin\theta \qquad\text{(vertical component, m s⁻¹)}
\end{aligned}
\]

Because there is no horizontal force, \(u_x\) remains constant throughout the flight.

---

### 3. Write the kinematic equations for each direction  

**Horizontal (x‑direction)** – constant velocity:

\[
x(t)=u_x\,t = (u\cos\theta)\,t \tag{1}
\]

**Vertical (y‑direction)** – constant downward acceleration \(-g\):

\[
y(t)=u_y\,t-\frac{1}{2}gt^{2}
      = (u\sin\theta)\,t-\frac{1}{2}gt^{2} \tag{2}
\]

The origin \((x=0,\;y=0)\) is taken at the launch point.

---

### 4. Find the **time of flight** \(T\)

The projectile lands when it returns to the launch height, i.e. when \(y(T)=0\).

Set equation (2) to zero (excluding the trivial solution \(t=0\)):

\[
0 = (u\sin\theta)T-\frac{1}{2}gT^{2}
\]

Factor out \(T\neq0\):

\[
T\Bigl(u\sin\theta-\frac{1}{2}gT\Bigr)=0
\]

\[
\Rightarrow\; T = \frac{2u\sin\theta}{g} \tag{3}
\]

This is the total time the projectile spends in the air.

---

### 5. Compute the horizontal range \(R\)

Insert the flight time \(T\) from (3) into the horizontal displacement (1):

\[
\begin{aligned}
R &= x(T) = (u\cos\theta)\,T \\
  &= (u\cos\theta)\left(\frac{2u\sin\theta}{g}\right) \\
  &= \frac{2u^{2}\sin\theta\cos\theta}{g}
\end{aligned}
\]

---

### 6. Use the double‑angle identity

Recall the trigonometric identity  

\[
\sin(2\theta)=2\sin\theta\cos\theta .
\]

Replace the product \(2\sin\theta\cos\theta\) in the expression for \(R\):

\[
R = \frac{u^{2}\,\sin(2\theta)}{g}.
\]

---

### 7. Final result

\[
\boxed{\,R=\dfrac{u^{2}\,\sin(2\theta)}{g}\,}
\]

- **Units check:**  
  \(u^{2}\) has units \((\text{m s}^{-1})^{2}= \text{m}^{2}\text{s}^{-2}\).  
  \(\sin(2\theta)\) is dimensionless.  
  Dividing by \(g\) (units m s⁻²) leaves units of metres, as required for a distance.

---

### 8. Quick sanity checks  

* **Maximum range:** \(\sin(2\theta)\) attains its maximum value 1 when \(2\theta = 90^{\circ}\) → \(\theta = 45^{\circ}\). Hence the longest possible range for a given speed \(u\) is \(R_{\max}=u^{2}/g\).  
* **Zero range:** If \(\theta = 0^{\circ}\) (horizontal launch) or \(\theta = 90^{\circ}\) (straight up), \(\sin(2\theta)=0\) and the projectile lands where it started, as expected.

---

**Summary of steps**

1. Resolve the launch velocity into horizontal and vertical components.  
2. Write the constant‑velocity horizontal equation and the uniformly‑accelerated vertical equation.  
3. Set the vertical displacement to zero to find the total flight time \(T\).  
4. Substitute \(T\) into the horizontal equation to obtain the range.  
5. Apply the double‑angle identity to arrive at the compact formula \(R = u^{2}\sin(2\theta)/g\).

Feel free to ask if any part needs more detail (e.g., what changes if the launch and landing heights differ, or if air resistance is included).
