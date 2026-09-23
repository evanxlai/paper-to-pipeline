-- binary-trees, after the Computer Language Benchmarks Game program of the
-- same name. It allocates and walks many small binary trees, so the run is
-- dominated by table allocation, recursion and the garbage collector.
--
-- N is the depth of the deepest tree (at least 4). The work roughly
-- doubles with each step of N. The Benchmarks Game program floors N at 6.
-- This one floors it at 4, because depth 6 already costs about 6.6 M
-- instructions and the smoke size must be smaller than that.
--
-- The check needs no reference output: a full binary tree of depth d has
-- 2^(d+1) - 1 nodes, so every count the script prints has a closed form.
-- The script returns true only if every count matches it.

local function bottom_up_tree(depth)
  if depth > 0 then
    depth = depth - 1
    return { bottom_up_tree(depth), bottom_up_tree(depth) }
  end
  return {}
end

local function item_check(tree)
  if tree[1] then
    return 1 + item_check(tree[1]) + item_check(tree[2])
  end
  return 1
end

local ok = true
local function expect(trees, depth, check)
  if check ~= trees * ((1 << (depth + 1)) - 1) then
    ok = false
  end
end

local min_depth = 4
local max_depth = math.max(min_depth, N)

local stretch_depth = max_depth + 1
local stretch_check = item_check(bottom_up_tree(stretch_depth))
print(string.format("stretch tree of depth %d\t check: %d",
                    stretch_depth, stretch_check))
expect(1, stretch_depth, stretch_check)

local long_lived = bottom_up_tree(max_depth)

for depth = min_depth, max_depth, 2 do
  local trees = 1 << (max_depth - depth + min_depth)
  local check = 0
  for _ = 1, trees do
    check = check + item_check(bottom_up_tree(depth))
  end
  print(string.format("%d\t trees of depth %d\t check: %d",
                      trees, depth, check))
  expect(trees, depth, check)
end

local long_check = item_check(long_lived)
print(string.format("long lived tree of depth %d\t check: %d",
                    max_depth, long_check))
expect(1, max_depth, long_check)

return ok
