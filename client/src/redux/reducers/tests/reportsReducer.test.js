import { reportsTypes } from '../../constants/index';
import reportsReducer from '../reportsReducer';

const initialState = {
  persist: {},

  search: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    reports: []
  }
};

describe('ReportsReducer', function() {
  it('should return the initial state', () => {
    expect(reportsReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle GET_REPORTS_REJECTED', () => {
    let dispatched = {
      type: reportsTypes.GET_REPORTS_REJECTED,
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          request: {
            responseText: 'GET ERROR'
          }
        }
      }
    };

    let resultState = reportsReducer(undefined, dispatched);
    expect(resultState.search.error).toBeTruthy();
    expect(resultState.search.errorMessage).toEqual('GET ERROR');

    expect(resultState.persist).toEqual(initialState.persist);
  });

  it('should handle GET_REPORTS_PENDING', () => {
    let dispatched = {
      type: reportsTypes.GET_REPORTS_PENDING
    };

    let resultState = reportsReducer(undefined, dispatched);

    expect(resultState.search.pending).toBeTruthy();
    expect(resultState.persist).toEqual(initialState.persist);
  });

  it('should handle GET_REPORTS_FULFILLED', () => {
    let dispatched = {
      type: reportsTypes.GET_REPORTS_FULFILLED,
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

    expect(resultState.search.fulfilled).toBeTruthy();
    expect(resultState.search.reports).toHaveLength(4);

    expect(resultState.persist).toEqual(initialState.persist);
  });
});
