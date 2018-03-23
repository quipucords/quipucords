import helpers from '../../../common/helpers';
import { reportsTypes } from '../../constants/index';
import reportsReducer from '../reportsReducer';

const initialState = {
  error: false,
  errorMessage: '',
  pending: false,
  fulfilled: false,
  reports: []
};

describe('ReportsReducer', function() {
  it('should return the initial state', () => {
    expect(reportsReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle GET_REPORT_REJECTED', () => {
    let dispatched = {
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

    let resultState = reportsReducer(undefined, dispatched);
    expect(resultState.error).toBeTruthy();
    expect(resultState.errorMessage).toEqual('GET ERROR');
    expect(resultState.pending).toBeFalsy();
    expect(resultState.fulfilled).toBeFalsy();
    expect(resultState.reports).toHaveLength(0);

    expect(resultState.persist).toEqual(initialState.persist);
  });

  it('should handle GET_REPORT_PENDING', () => {
    let dispatched = {
      type: helpers.PENDING_ACTION(reportsTypes.GET_REPORT)
    };

    let resultState = reportsReducer(undefined, dispatched);

    expect(resultState.error).toBeFalsy();
    expect(resultState.errorMessage).toEqual('');
    expect(resultState.pending).toBeTruthy();
    expect(resultState.fulfilled).toBeFalsy();
    expect(resultState.reports).toHaveLength(0);
  });

  it('should handle GET_REPORT_FULFILLED', () => {
    let dispatched = {
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

    let resultState = reportsReducer(undefined, dispatched);

    expect(resultState.error).toBeFalsy();
    expect(resultState.errorMessage).toEqual('');
    expect(resultState.pending).toBeFalsy();
    expect(resultState.fulfilled).toBeTruthy();
    expect(resultState.reports).toHaveLength(4);
  });
});
