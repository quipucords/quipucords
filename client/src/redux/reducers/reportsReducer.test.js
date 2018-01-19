import { reportsTypes as types } from '../constants';
import reportsReducer from './reportsReducer';

describe('ReportsReducer', function() {
  it('should return the initial state', () => {
    const initialState = {
      error: false,
      errorMessage: '',
      loading: true,
      data: []
    };

    expect(reportsReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle GET_REPORTS_ERROR', () => {
    const dispatched = {
      type: types.GET_REPORTS_ERROR,
      error: true,
      message: 'error message'
    };

    expect(reportsReducer(undefined, dispatched).error).toEqual(
      dispatched.error
    );
    expect(reportsReducer(undefined, dispatched).errorMessage).toEqual(
      dispatched.message
    );
  });

  it('should handle GET_REPORTS_LOADING', () => {
    const dispatched = {
      type: types.GET_REPORTS_LOADING,
      loading: false
    };

    expect(reportsReducer(undefined, dispatched).loading).toEqual(
      dispatched.loading
    );
  });

  it('should handle GET_REPORTS_SUCCESS', () => {
    const dispatched = {
      type: types.GET_REPORTS_SUCCESS,
      data: ['test']
    };

    expect(reportsReducer(undefined, dispatched).data).toEqual(dispatched.data);
  });
});
