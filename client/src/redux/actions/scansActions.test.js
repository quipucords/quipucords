import { scansTypes as types } from '../constants';
import * as actions from './scansActions';

describe('ScansActions', function() {
  it('should create a GET error action', () => {
    const error = true;
    const expectedAction = {
      type: types.GET_SCANS_ERROR,
      error,
      message: undefined
    };

    expect(actions.getScansError(error)).toEqual(expectedAction);
  });

  it('should create a GET loading action', () => {
    const loading = true;
    const expectedAction = {
      type: types.GET_SCANS_LOADING,
      loading
    };

    expect(actions.getScansLoading(loading)).toEqual(expectedAction);
  });

  it('should create a GET success action', () => {
    const data = {};
    const expectedAction = {
      type: types.GET_SCANS_SUCCESS,
      data
    };

    expect(actions.getScansSuccess(data)).toEqual(expectedAction);
  });
});
