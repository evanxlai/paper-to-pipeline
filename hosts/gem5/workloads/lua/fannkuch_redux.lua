-- fannkuch-redux, after the Computer Language Benchmarks Game program of
-- the same name. It walks every permutation of 1..N and, for each one,
-- counts the prefix reversals ("pancake flips") needed to bring 1 to the
-- front. The loops are short, and when they exit depends on the data. That
-- makes this the most branch-bound of the Lua scripts.
--
-- N is the permutation length (at least 3). The work grows as N!, so one
-- step of N multiplies it by N. M (default 1) repeats the whole run M
-- times, which gives the sizes in between. Every repeat is checked.
--
-- The check compares the checksum and the largest flip count with a table
-- of reference values for N from 3 to 12. N = 7 and N = 12 are the
-- benchmark's published outputs. N = 3 to 11 were also computed by a
-- separate Python version of the reference C program's permutation
-- order, and they agree. For any other N the script prints the values and
-- passes, so a retuned size still runs.

local function fannkuch(n)
  local perm, flip, count = {}, {}, {}
  for i = 1, n do
    perm[i], flip[i], count[i] = i, i, i
  end
  local sign, max_flips, checksum = 1, 0, 0

  while true do
    -- Count the flips for this permutation.
    local first = perm[1]
    if first ~= 1 then
      for i = 2, n do
        flip[i] = perm[i]
      end
      local flips = 1
      while true do
        local next_first = flip[first]
        if next_first == 1 then
          checksum = checksum + sign * flips
          if flips > max_flips then
            max_flips = flips
          end
          break
        end
        flip[first] = first
        if first >= 4 then
          local i, j = 2, first - 1
          repeat
            flip[i], flip[j] = flip[j], flip[i]
            i, j = i + 1, j - 1
          until i >= j
        end
        first = next_first
        flips = flips + 1
      end
    end

    -- Step to the next permutation, alternating the sign of the checksum.
    if sign == 1 then
      perm[1], perm[2] = perm[2], perm[1]
      sign = -1
    else
      perm[2], perm[3] = perm[3], perm[2]
      sign = 1
      for i = 3, n do
        local c = count[i]
        if c ~= 1 then
          count[i] = c - 1
          break
        end
        if i == n then
          return checksum, max_flips
        end
        count[i] = i
        local head = perm[1]
        for j = 1, i do
          perm[j] = perm[j + 1]
        end
        perm[i + 1] = head
      end
    end
  end
end

local known = {
  [3] = {2, 2}, [4] = {4, 4}, [5] = {11, 7}, [6] = {49, 10},
  [7] = {228, 16}, [8] = {1616, 22}, [9] = {8629, 30},
  [10] = {73196, 38}, [11] = {556355, 51}, [12] = {3968050, 65},
}

local n = math.max(3, N)
local want = known[n]
local ok = true
local checksum, max_flips
for _ = 1, M do
  checksum, max_flips = fannkuch(n)
  if want and (checksum ~= want[1] or max_flips ~= want[2]) then
    ok = false
  end
end
print(checksum)
print(string.format("Pfannkuchen(%d) = %d", n, max_flips))
if want == nil then
  print("no reference value for this N; checksum not compared")
end
return ok
