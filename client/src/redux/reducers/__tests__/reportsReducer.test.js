import helpers from '../../../common/helpers';
import { reportsTypes } from '../../constants/index';
import reportsReducer from '../reportsReducer';

const initialState = {
  report: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    reports: []
  },

  merge: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false
  }
};

describe('ReportsReducer', () => {
  it('should return the initial state', () => {
    expect(reportsReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle GET_REPORT_REJECTED', () => {
    const dispatched = {
      type: helpers.REJECTED_ACTION(reportsTypes.GET_REPORT),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'GET ERROR'
          }
        }
      }
    };

    const resultState = reportsReducer(undefined, dispatched);
    expect(resultState.report.error).toBeTruthy();
    expect(resultState.report.errorMessage).toEqual('GET ERROR');
    expect(resultState.report.pending).toBeFalsy();
    expect(resultState.report.fulfilled).toBeFalsy();
    expect(resultState.report.reports).toHaveLength(0);

    expect(resultState.report.persist).toEqual(initialState.report.persist);
  });

  it('should handle GET_REPORT_PENDING', () => {
    const dispatched = {
      type: helpers.PENDING_ACTION(reportsTypes.GET_REPORT)
    };

    const resultState = reportsReducer(undefined, dispatched);

    expect(resultState.report.error).toBeFalsy();
    expect(resultState.report.errorMessage).toEqual('');
    expect(resultState.report.pending).toBeTruthy();
    expect(resultState.report.fulfilled).toBeFalsy();
    expect(resultState.report.reports).toHaveLength(0);
  });

  it('should handle GET_REPORT_FULFILLED', () => {
    const dispatched = {
      type: helpers.FULFILLED_ACTION(reportsTypes.GET_REPORT),
      payload: {
        data: [
          {
            name: '1',
            id: 1
          },
          {
            name: '2',
            id: 2
          },
          {
            name: '3',
            id: 3
          },
          {
            name: '4',
            id: 4
          }
        ]
      }
    };

    const resultState = reportsReducer(undefined, dispatched);

    expect(resultState.report.error).toBeFalsy();
    expect(resultState.report.errorMessage).toEqual('');
    expect(resultState.report.pending).toBeFalsy();
    expect(resultState.report.fulfilled).toBeTruthy();
    expect(resultState.report.reports).toHaveLength(4);
  });
});
