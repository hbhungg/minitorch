from itertools import product
import numpy as np
from .tensor_data import (
  to_index,
  index_to_position,
  broadcast_index,
  shape_broadcast,
  MAX_DIMS,
)


def tensor_map(fn):
  """
  Low-level implementation of tensor map between
  tensors with *possibly different strides*.

  Simple version:

  * Fill in the `out` array by applying `fn` to each
    value of `in_storage` assuming `out_shape` and `in_shape`
    are the same size.

  Broadcasted version:

  * Fill in the `out` array by applying `fn` to each
    value of `in_storage` assuming `out_shape` and `in_shape`
    broadcast. (`in_shape` must be smaller than `out_shape`).

  Args:
    fn: function from float-to-float to apply
    out (array): storage for out tensor
    out_shape (array): shape for out tensor
    out_strides (array): strides for out tensor
    in_storage (array): storage for in tensor
    in_shape (array): shape for in tensor
    in_strides (array): strides for in tensor

  Returns:
    None : Fills in `out`
  """

  def _map(out, out_shape, out_strides, in_storage, in_shape, in_strides):
    in_bidx = np.array(in_shape)
    for idx in product(*(range(i) for i in out_shape)):
      broadcast_index(idx, out_shape, in_shape, in_bidx)
      in_val = in_storage[index_to_position(in_bidx, in_strides)]
      out[index_to_position(idx, out_strides)] = fn(in_val)
  return _map


def map(fn):
  """
  Higher-order tensor map function ::

    fn_map = map(fn)
    fn_map(a, out)
    out

  Simple version::

    for i:
      for j:
        out[i, j] = fn(a[i, j])

  Broadcasted version (`a` might be smaller than `out`) ::

    for i:
      for j:
        out[i, j] = fn(a[i, 0])

  Args:
    fn: function from float-to-float to apply.
    a (:class:`TensorData`): tensor to map over
    out (:class:`TensorData`): optional, tensor data to fill in,
         should broadcast with `a`

  Returns:
    :class:`TensorData` : new tensor data
  """

  f = tensor_map(fn)

  def ret(a, out=None):
    if out is None:
      out = a.zeros(a.shape)
    f(*out.tuple(), *a.tuple())
    return out

  return ret


def tensor_zip(fn):
  """
  Low-level implementation of tensor zip between
  tensors with *possibly different strides*.

  Simple version:

  * Fill in the `out` array by applying `fn` to each
    value of `a_storage` and `b_storage` assuming `out_shape`
    and `a_shape` are the same size.

  Broadcasted version:

  * Fill in the `out` array by applying `fn` to each
    value of `a_storage` and `b_storage` assuming `a_shape`
    and `b_shape` broadcast to `out_shape`.

  Args:
    fn: function mapping two floats to float to apply
    out (array): storage for `out` tensor
    out_shape (array): shape for `out` tensor
    out_strides (array): strides for `out` tensor
    a_storage (array): storage for `a` tensor
    a_shape (array): shape for `a` tensor
    a_strides (array): strides for `a` tensor
    b_storage (array): storage for `b` tensor
    b_shape (array): shape for `b` tensor
    b_strides (array): strides for `b` tensor

  Returns:
    None : Fills in `out`
  """

  def _zip(
    out, out_shape, out_strides,
    a_storage, a_shape, a_strides,
    b_storage, b_shape, b_strides):
    # Same as map
    a_bidx = np.array(a_shape)
    b_bidx = np.array(b_shape)
    for idx in product(*(range(i) for i in out_shape)):
      broadcast_index(idx, out_shape, a_shape, a_bidx)
      broadcast_index(idx, out_shape, b_shape, b_bidx)
      a_val = a_storage[index_to_position(a_bidx, a_strides)]
      b_val = b_storage[index_to_position(b_bidx, b_strides)]
      out[index_to_position(idx, out_strides)] = fn(a_val, b_val)
  return _zip


def zip(fn):
  """
  Higher-order tensor zip function ::

    fn_zip = zip(fn)
    out = fn_zip(a, b)

  Simple version ::

    for i:
      for j:
        out[i, j] = fn(a[i, j], b[i, j])

  Broadcasted version (`a` and `b` might be smaller than `out`) ::

    for i:
      for j:
        out[i, j] = fn(a[i, 0], b[0, j])


  Args:
    fn: function from two floats-to-float to apply
    a (:class:`TensorData`): tensor to zip over
    b (:class:`TensorData`): tensor to zip over

  Returns:
    :class:`TensorData` : new tensor data
  """

  f = tensor_zip(fn)

  def ret(a, b):
    if a.shape != b.shape:
      c_shape = shape_broadcast(a.shape, b.shape)
    else:
      c_shape = a.shape
    out = a.zeros(c_shape)
    f(*out.tuple(), *a.tuple(), *b.tuple())
    return out

  return ret


def tensor_reduce(fn):
  """
  Low-level implementation of tensor reduce.

  * `out_shape` will be the same as `in_shape`
     except with `reduce_dim` turned to size `1`

  Args:
    fn: reduction function mapping two floats to float
    out (array): storage for `out` tensor
    out_shape (array): shape for `out` tensor
    out_strides (array): strides for `out` tensor
    in_storage (array): storage for `a` tensor
    in_shape (array): shape for `a` tensor
    in_strides (array): strides for `a` tensor
    reduce_dim (int): dimension to reduce out

  Returns:
    None : Fills in `out`
  """

  def _reduce(out, out_shape, out_strides, in_storage, in_shape, in_strides, reduce_dim):
    # For each of the idxs, loop through all of the reduced dim idx to "collapse" that dim
    for idx in product(*(range(i) for i in np.delete(in_shape, reduce_dim))):
      last = None
      for reduce_idx in range(in_shape[reduce_dim]):
        full_idx = idx[:reduce_dim] + (reduce_idx,) + idx[reduce_dim:]
        val = in_storage[index_to_position(full_idx, in_strides)]
        if last is None:
          last = val
        else:
          last = fn(last, val)

      # Idx of the out tensor (reduced)
      out_idx = idx[:reduce_dim] + (0,) + idx[reduce_dim:]
      out[index_to_position(out_idx, out_strides)] = last
  return _reduce


def reduce(fn, start=0.0):
  """
  Higher-order tensor reduce function. ::

    fn_reduce = reduce(fn)
    out = fn_reduce(a, dim)

  Simple version ::

    for j:
      out[1, j] = start
      for i:
        out[1, j] = fn(out[1, j], a[i, j])


  Args:
    fn: function from two floats-to-float to apply
    a (:class:`TensorData`): tensor to reduce over
    dim (int): int of dim to reduce

  Returns:
    :class:`TensorData` : new tensor
  """
  f = tensor_reduce(fn)

  def ret(a, dim):
    out_shape = list(a.shape)
    out_shape[dim] = 1

    # Other values when not sum.
    out = a.zeros(tuple(out_shape))
    out._tensor._storage[:] = start

    f(*out.tuple(), *a.tuple(), dim)
    return out

  return ret


class TensorOps:
  map = map
  zip = zip
  reduce = reduce
