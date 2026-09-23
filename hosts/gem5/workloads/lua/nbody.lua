-- n-body, after the Computer Language Benchmarks Game program of the same
-- name. It integrates the orbits of the four gas giants around the sun.
-- The work is floating-point arithmetic on table fields. The branches are
-- mostly loop control, which makes this the regular end of the Lua set.
--
-- N is the number of time steps. The work grows linearly with N.
--
-- The check has two parts. The starting energy must print as the published
-- value -0.169075164. Then the energy after N steps must stay within 0.1%
-- of it, because the integrator conserves energy that well over any size
-- this workload uses. The exact final value is in expected.json.

local sqrt = math.sqrt

local PI = math.pi
local SOLAR_MASS = 4 * PI * PI
local DAYS_PER_YEAR = 365.24

local function body(x, y, z, vx, vy, vz, mass)
  return {
    x = x, y = y, z = z,
    vx = vx * DAYS_PER_YEAR, vy = vy * DAYS_PER_YEAR, vz = vz * DAYS_PER_YEAR,
    mass = mass * SOLAR_MASS,
  }
end

local bodies = {
  body(0, 0, 0, 0, 0, 0, 1),                          -- sun
  body(4.84143144246472090e+00, -1.16032004402742839e+00,
       -1.03622044471123109e-01, 1.66007664274403694e-03,
       7.69901118419740425e-03, -6.90460016972063023e-05,
       9.54791938424326609e-04),                      -- jupiter
  body(8.34336671824457987e+00, 4.12479856412430479e+00,
       -4.03523417114321381e-01, -2.76742510726862411e-03,
       4.99852801234917238e-03, 2.30417297573763929e-05,
       2.85885980666130812e-04),                      -- saturn
  body(1.28943695621391310e+01, -1.51111514016986312e+01,
       -2.23307578892655734e-01, 2.96460137564761618e-03,
       2.37847173959480950e-03, -2.96589568540237556e-05,
       4.36624404335156298e-05),                      -- uranus
  body(1.53796971148509165e+01, -2.59193146099879641e+01,
       1.79258772950371181e-01, 2.68067772490389322e-03,
       1.62824170038242295e-03, -9.51592254519715870e-05,
       5.15138902046611451e-05),                      -- neptune
}

local function advance(nbody, dt)
  for i = 1, nbody do
    local bi = bodies[i]
    local bix, biy, biz, bimass = bi.x, bi.y, bi.z, bi.mass
    local bivx, bivy, bivz = bi.vx, bi.vy, bi.vz
    for j = i + 1, nbody do
      local bj = bodies[j]
      local dx, dy, dz = bix - bj.x, biy - bj.y, biz - bj.z
      local d2 = dx * dx + dy * dy + dz * dz
      local mag = dt / (d2 * sqrt(d2))
      local bm = bj.mass * mag
      bivx = bivx - dx * bm
      bivy = bivy - dy * bm
      bivz = bivz - dz * bm
      bm = bimass * mag
      bj.vx = bj.vx + dx * bm
      bj.vy = bj.vy + dy * bm
      bj.vz = bj.vz + dz * bm
    end
    bi.vx, bi.vy, bi.vz = bivx, bivy, bivz
    bi.x = bix + dt * bivx
    bi.y = biy + dt * bivy
    bi.z = biz + dt * bivz
  end
end

local function energy(nbody)
  local e = 0
  for i = 1, nbody do
    local bi = bodies[i]
    local vx, vy, vz, bim = bi.vx, bi.vy, bi.vz, bi.mass
    e = e + 0.5 * bim * (vx * vx + vy * vy + vz * vz)
    for j = i + 1, nbody do
      local bj = bodies[j]
      local dx, dy, dz = bi.x - bj.x, bi.y - bj.y, bi.z - bj.z
      e = e - bim * bj.mass / sqrt(dx * dx + dy * dy + dz * dz)
    end
  end
  return e
end

local function offset_momentum(nbody)
  local px, py, pz = 0, 0, 0
  for i = 1, nbody do
    local b = bodies[i]
    local bim = b.mass
    px = px + b.vx * bim
    py = py + b.vy * bim
    pz = pz + b.vz * bim
  end
  bodies[1].vx = -px / SOLAR_MASS
  bodies[1].vy = -py / SOLAR_MASS
  bodies[1].vz = -pz / SOLAR_MASS
end

local nbody = #bodies
offset_momentum(nbody)
local e0 = energy(nbody)
local start = string.format("%0.9f", e0)
print(start)
for _ = 1, N do
  advance(nbody, 0.01)
end
local e1 = energy(nbody)
print(string.format("%0.9f", e1))

return start == "-0.169075164" and math.abs(e1 - e0) < 1e-3 * math.abs(e0)
