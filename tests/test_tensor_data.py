import minitorch
from hypothesis import given
from hypothesis.strategies import data
from .strategies import tensor_data, indices
import pytest

# ## Tasks 2.1

# Check basic properties of layout and strides.


@pytest.mark.task2_1
def test_layout():
  "Test basis properties of layout and strides"
  data = [0] * 3 * 5
  tensor_data = minitorch.TensorData(data, (3, 5), (5, 1))

  assert tensor_data.is_contiguous()
  assert tensor_data.shape == (3, 5)
  assert tensor_data.index((1, 0)) == 5
  assert tensor_data.index((1, 2)) == 7

  tensor_data = minitorch.TensorData(data, (5, 3), (1, 5))
  assert tensor_data.shape == (5, 3)
  assert not tensor_data.is_contiguous()

  data = [0] * 4 * 2 * 2
  tensor_data = minitorch.TensorData(data, (4, 2, 2))
  assert tensor_data.strides == (4, 2, 1)


@pytest.mark.xfail
def test_layout_bad():
  "Test basis properties of layout and strides"
  data = [0] * 3 * 5
  minitorch.TensorData(data, (3, 5), (6,))


@pytest.mark.task2_1
@given(tensor_data())
def test_enumeration(tensor_data):
  "Test enumeration of tensor_datas."
  indices = list(tensor_data.indices())

  # Check that enough positions are enumerated.
  assert len(indices) == tensor_data.size

  # Check that enough positions are enumerated only once.
  assert len(set(tensor_data.indices())) == len(indices)

  # Check that all indices are within the shape.
  for ind in tensor_data.indices():
    for i, p in enumerate(ind):
      assert p >= 0 and p < tensor_data.shape[i]


@pytest.mark.task2_1
@given(tensor_data())
def test_index(tensor_data):
  "Test enumeration of tensor_data."
  # Check that all indices are within the size.
  for ind in tensor_data.indices():
    pos = tensor_data.index(ind)
    assert pos >= 0 and pos < tensor_data.size

  base = [0] * tensor_data.dims
  with pytest.raises(minitorch.IndexingError):
    base[0] = -1
    tensor_data.index(tuple(base))

  if tensor_data.dims > 1:
    with pytest.raises(minitorch.IndexingError):
      base = [0] * (tensor_data.dims - 1)
      tensor_data.index(tuple(base))


@pytest.mark.task2_1
@given(data())
def test_permute(data):
  td = data.draw(tensor_data())
  ind = data.draw(indices(td))
  td_rev = td.permute(*list(reversed(range(td.dims))))
  assert td.index(ind) == td_rev.index(tuple(reversed(ind)))

  td2 = td_rev.permute(*list(reversed(range(td_rev.dims))))
  assert td.index(ind) == td2.index(ind)


# ## Tasks 2.2

# Check basic properties of broadcasting.


@pytest.mark.task2_2
def test_shape_broadcast():
  c = minitorch.shape_broadcast((1,), (5, 5))
  assert c == (5, 5)

  c = minitorch.shape_broadcast((5, 5), (1,))
  assert c == (5, 5)

  c = minitorch.shape_broadcast((1, 5, 5), (5, 5))
  assert c == (1, 5, 5)

  c = minitorch.shape_broadcast((5, 1, 5, 1), (1, 5, 1, 5))
  assert c == (5, 5, 5, 5)

  with pytest.raises(minitorch.IndexingError):
    c = minitorch.shape_broadcast((5, 7, 5, 1), (1, 5, 1, 5))
    print(c)

  with pytest.raises(minitorch.IndexingError):
    c = minitorch.shape_broadcast((5, 2), (5,))
    print(c)

  c = minitorch.shape_broadcast((2, 5), (5,))
  assert c == (2, 5)


@pytest.mark.task2_2
def test_broadcast_index():
  import numpy as np

  out = np.array([0, 0])
  
  # TODO: This whole thing could be automated by hypothesis?
  # Broadcast in s1
  big_shape1 = (1, 5, 5)
  small_shape1 = (1, 5)
  # Broadcast in s2
  big_shape2 = (1, 5, 5)
  small_shape2 = (5, 1)

  for s1 in range(5):
    for s2 in range(5):
      # Broadcast in s1
      minitorch.broadcast_index((0, s1, s2), big_shape1, small_shape1, out)
      assert np.array_equal(out, np.array([0, s2]))

      # Broadcast in s2
      minitorch.broadcast_index((0, s1, s2), big_shape2, small_shape2, out)
      assert np.array_equal(out, np.array([s1, 0]))


@given(tensor_data())
def test_string(tensor_data):
  tensor_data.to_string()
