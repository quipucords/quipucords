import { scansReducer } from '../scansReducer';
import { scansTypes as types } from '../../constants';
import helpers from '../../../common/helpers';

describe('ScansReducer', () => {
  it('should return the initial state', () => {
    expect(scansReducer.initialState).toBeDefined();
  });

  it('should handle specific defined types', () => {
    const specificTypes = [types.RESET_SCAN_ADD_STATUS, types.MERGE_SCAN_DIALOG_SHOW, types.MERGE_SCAN_DIALOG_HIDE];

    specificTypes.forEach(value => {
      const dispatched = {
        type: value
      };

      const resultState = scansReducer(undefined, dispatched);

      expect({ type: value, result: resultState }).toMatchSnapshot(`defined type ${value}`);
    });
  });

  it('should handle all defined error types', () => {
    const specificTypes = [
      types.GET_SCANS,
      types.GET_SCAN,
      types.GET_SCAN_CONNECTION_RESULTS,
      types.GET_SCAN_INSPECTION_RESULTS,
      types.GET_SCAN_JOBS,
      types.ADD_SCAN,
      types.START_SCAN,
      types.CANCEL_SCAN,
      types.PAUSE_SCAN,
      types.RESTART_SCAN,
      types.DELETE_SCAN
    ];

    specificTypes.forEach(value => {
      const dispatched = {
        type: helpers.REJECTED_ACTION(value),
        error: true,
        payload: {
          message: 'MESSAGE',
          response: {
            status: 0,
            statusText: 'ERROR TEST',
            data: {
              detail: 'ERROR'
            }
          }
        }
      };

      const resultState = scansReducer(undefined, dispatched);

      expect({ type: helpers.REJECTED_ACTION(value), result: resultState }).toMatchSnapshot(`rejected types ${value}`);
    });
  });

  it('should handle all defined pending types', () => {
    const specificTypes = [
      types.GET_SCANS,
      types.GET_SCAN,
      types.GET_SCAN_CONNECTION_RESULTS,
      types.GET_SCAN_INSPECTION_RESULTS,
      types.GET_SCAN_JOBS,
      types.ADD_SCAN,
      types.START_SCAN,
      types.CANCEL_SCAN,
      types.PAUSE_SCAN,
      types.RESTART_SCAN,
      types.DELETE_SCAN
    ];

    specificTypes.forEach(value => {
      const dispatched = {
        type: helpers.PENDING_ACTION(value)
      };

      const resultState = scansReducer(undefined, dispatched);

      expect({ type: helpers.PENDING_ACTION(value), result: resultState }).toMatchSnapshot(`pending types ${value}`);
    });
  });

  it('should handle all defined fulfilled types', () => {
    const specificTypes = [
      types.GET_SCANS,
      types.GET_SCAN,
      types.GET_SCAN_CONNECTION_RESULTS,
      types.GET_SCAN_INSPECTION_RESULTS,
      types.GET_SCAN_JOBS,
      types.ADD_SCAN,
      types.START_SCAN,
      types.CANCEL_SCAN,
      types.PAUSE_SCAN,
      types.RESTART_SCAN,
      types.DELETE_SCAN
    ];

    specificTypes.forEach(value => {
      const dispatched = {
        type: helpers.FULFILLED_ACTION(value),
        payload: {
          data: {
            test: 'success'
          }
        }
      };

      const resultState = scansReducer(undefined, dispatched);

      expect({ type: helpers.FULFILLED_ACTION(value), result: resultState }).toMatchSnapshot(
        `fulfilled types ${value}`
      );
    });
  });
});
