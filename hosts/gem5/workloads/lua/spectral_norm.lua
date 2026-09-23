-- spectral-norm, after the Computer Language Benchmarks Game program of
-- the same name. It estimates the largest singular value of an infinite
-- matrix by power iteration on its N by N corner. The inner loops call a
-- small function for every matrix element, so the run exercises Lua calls
-- and floating-point division.
--
-- N is the matrix size (at least 10). The work grows as N squared.
--
-- The check: the estimate converges to 1.2742241 quickly as N grows. For
-- N of 10 and up it is within 0.005 of that limit. The exact printed value
-- is in expected.json.

local function A(i, j)
  local ij = i + j - 1
  return 1.0 / (ij * (ij - 1) * 0.5 + i)
end

local function Av(x, y, n)
  for i = 1, n do
    local a = 0
    for j = 1, n do
      a = a + x[j] * A(i, j)
    end
    y[i] = a
  end
end

local function Atv(x, y, n)
  for i = 1, n do
    local a = 0
    for j = 1, n do
      a = a + x[j] * A(j, i)
    end
    y[i] = a
  end
end

local function AtAv(x, y, t, n)
  Av(x, t, n)
  Atv(t, y, n)
end

local n = math.max(10, N)
local u, v, t = {}, {}, {}
for i = 1, n do
  u[i] = 1
end
for _ = 1, 10 do
  AtAv(u, v, t, n)
  AtAv(v, u, t, n)
end

local vBv, vv = 0, 0
for i = 1, n do
  local ui, vi = u[i], v[i]
  vBv = vBv + ui * vi
  vv = vv + vi * vi
end
local norm = math.sqrt(vBv / vv)
print(string.format("%0.9f", norm))

return math.abs(norm - 1.2742241) < 0.005
