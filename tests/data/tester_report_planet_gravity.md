**Why the surface gravity is different on each planet**

The strength of the gravitational pull that you feel on the surface of a planet is called the **surface gravity** (often written $g$).  
For a spherically‑symmetric body the value of $g$ at the surface is given by the simple Newtonian formula  

$$\boxed{g = \frac{G\,M}{R^{2}}}$$

where  

* $G = 6.674\times10^{-11}\ {\rm N\,m^{2}\,kg^{-2}}$ is the universal gravitational constant,  
* $M$ is the **mass** of the planet (in kilograms, kg), and  
* $R$ is the **radius** of the planet (in metres, m).  

Thus the surface gravity depends on **two things**:

1. **How much matter the planet contains** (its mass).  
2. **How far that matter is from you** (the distance to the planet’s centre, i.e. the radius).

A planet that is very massive will pull more strongly, but if it is also very large the pull is “diluted’’ because the distance $R$ appears squared in the denominator. The net result is the balance of these two factors.

---

### 1. Mass vs. radius: a few examples  

| Planet | Mass $M$ (kg) | Mean radius $R$ (m) | Calculated $g$ (m s$^{-2}$) | Observed $g$ (m s$^{-2}$) |
|--------|----------------|-----------------------|-------------------------------|------------------------------|
| Mercury| $3.30\times10^{23}$ | $2.44\times10^{6}$ | 3.7 | 3.7 |
| Venus  | $4.87\times10^{24}$ | $6.05\times10^{6}$ | 8.9 | 8.9 |
| Earth  | $5.97\times10^{24}$ | $6.37\times10^{6}$ | 9.8 | 9.8 |
| Mars   | $6.42\times10^{23}$ | $3.39\times10^{6}$ | 3.7 | 3.7 |
| Jupiter| $1.90\times10^{27}$ | $6.99\times10^{7}$ | 24.8| 24.8 |
| Saturn | $5.68\times10^{26}$ | $5.82\times10^{7}$ | 10.4| 10.4 |
| Uranus | $8.68\times10^{25}$ | $2.54\times10^{7}$ | 8.9 | 8.9 |
| Neptune| $1.02\times10^{26}$ | $2.47\times10^{7}$ | 11.2| 11.2 |

*How the numbers arise:*  
Take Earth as an example  

$$g_{\oplus}= \frac{(6.674\times10^{-11})\,(5.97\times10^{24})}{(6.37\times10^{6})^{2}}
          \approx 9.8\ {\rm m\,s^{-2}} .$$

Jupiter is about 318 times more massive than Earth, but its radius is about 11 times larger.  
Because the radius is squared in the denominator, the increase in mass is only partially “canceled’’ by the larger size, giving a surface gravity roughly 2.5 times Earth’s.

---

### 2. Why the numbers differ from planet to planet  

| Factor | Effect on $g$ | Why it varies among planets |
|--------|----------------|-----------------------------|
| **Total mass $M$** | Directly proportional: double the mass → double $g$ (if radius unchanged). | Planets formed from different amounts of material; gas giants accreted huge envelopes of hydrogen/helium, while terrestrial planets are smaller. |
| **Radius $R$** | Inversely proportional to $R^{2}$: double the radius → one‑quarter the $g$ (if mass unchanged). | Composition matters: a planet made mostly of light gases expands to a large radius, reducing surface gravity despite a huge mass. |
| **Average density $\rho = M/(4\pi R^{3}/3)$** | Combining the two gives $g = \frac{4\pi G}{3}\,\rho\,R$. So for a given radius, a denser planet has larger $g$. | Rocky planets (Mercury, Earth) are denser than icy/gaseous ones, giving higher $g$ for a given size. |
| **Rotation** | The centrifugal acceleration $a_{\rm cf}= \omega^{2}r$ (where $\omega$ is angular speed, $r$ the distance from the rotation axis) reduces the *effective* gravity at the equator. | Fast rotators (e.g., Jupiter, Saturn) feel a few percent less gravity at the equator than at the poles. |
| **Shape (oblateness)** | An oblate planet has a larger equatorial radius, so $g$ is slightly smaller at the equator. | Rapid rotation flattens gas giants, enhancing the latitude dependence of $g$. |
| **Altitude** | Gravity falls off as $1/(R+h)^{2}$ where $h$ is height above the surface. | On any planet, climbing a mountain or flying in a high‑altitude aircraft reduces the local $g$ by a tiny amount. |

---

### 3. Putting it together – a simple “rule of thumb”

If you know a planet’s **mass** and **radius**, you can estimate its surface gravity with the formula above.  
A quick mental shortcut:

$$g \approx 9.8\ {\rm m\,s^{-2}}\;\times\;
\left(\frac{M/M_{\oplus}}{(R/R_{\oplus})^{2}}\right),$$

where $M_{\oplus}$ and $R_{\oplus}$ are Earth’s mass and radius.  
For example, Saturn’s mass is about 95 $M_{\oplus}$ and its radius about 9.5 $R_{\oplus}$:

$$g_{\rm Sat}\approx 9.8\;\frac{95}{(9.5)^{2}}\approx 10\ {\rm m\,s^{-2}} .$$

---

### 4. Summary  

*Surface gravity varies because planets differ in how much mass they contain **and** how that mass is distributed (size).  
*The governing equation $g = GM/R^{2}$ captures the balance between mass (pull) and radius (distance).  
*Additional modest effects come from rotation, shape, and altitude, but the dominant cause is the mass‑radius combination, which itself reflects each planet’s composition and formation history.*

If you’d like a deeper look at any particular planet (e.g., why Jupiter’s gravity isn’t 300 times Earth’s despite being 318 times more massive) or want to explore the role of rotation in more detail, just let me know!
