import { reportsTypes } from '../constants';
import * as actions from './reportsActions';

describe('ReportsActions', function() {
  it('should create a GET error action', () => {
    const error = true;
    const expectedAction = {
      type: reportsTypes.GET_REPORTS_ERROR,
      error,
      message: undefined
    };

    expect(actions.getReportsError(error)).toEqual(expectedAction);
  });

  it('should create a GET loading action', () => {
    const loading = true;
    const expectedAction = {
      type: reportsTypes.GET_REPORTS_LOADING,
      loading
    };

    expect(actions.getReportsLoading(loading)).toEqual(expectedAction);
  });

  it('should create a GET success action', () => {
    const data = {};
    const expectedAction = {
      type: reportsTypes.GET_REPORTS_SUCCESS,
      data
    };

    expect(actions.getReportsSuccess(data)).toEqual(expectedAction);
  });
});
