import { scansTypes as types } from '../constants';
import scansReducer from './scansReducer';

describe('ScansReducer', function() {
  it('should return the initial state', () => {
    const initialState = {
      error: false,
      errorMessage: '',
      loading: true,
      data: []
    };

    expect(scansReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle GET_SCANS_ERROR', () => {
    const dispatched = {
      type: types.GET_SCANS_ERROR,
      error: true,
      message: 'error message'
    };

    expect(scansReducer(undefined, dispatched).error).toEqual(dispatched.error);
    expect(scansReducer(undefined, dispatched).errorMessage).toEqual(
      dispatched.message
    );
  });

  it('should handle GET_SCANS_LOADING', () => {
    const dispatched = {
      type: types.GET_SCANS_LOADING,
      loading: false
    };

    expect(scansReducer(undefined, dispatched).loading).toEqual(
      dispatched.loading
    );
  });

  it('should handle GET_SCANS_SUCCESS', () => {
    const dispatched = {
      type: types.GET_SCANS_SUCCESS,
      data: ['test']
    };

    expect(scansReducer(undefined, dispatched).data).toEqual(dispatched.data);
  });
});
