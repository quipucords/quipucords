import addSourceWizardReducer from '../addSourceWizardReducer';
import { sourcesTypes as types, credentialsTypes } from '../../constants';
import helpers from '../../../common/helpers';

describe('AddSourceWizardReducer', () => {
  it('should return the initial state', () => {
    expect(addSourceWizardReducer.initialState).toBeDefined();
  });

  it('should handle specific defined types', () => {
    const specificTypes = [
      types.CREATE_SOURCE_SHOW,
      types.EDIT_SOURCE_SHOW,
      types.UPDATE_SOURCE_HIDE,
      types.VALID_SOURCE_WIZARD_STEPONE,
      types.VALID_SOURCE_WIZARD_STEPTWO
    ];

    specificTypes.forEach(value => {
      const dispatched = {
        type: value,
        source: {}
      };

      const resultState = addSourceWizardReducer(undefined, dispatched);

      expect({ type: value, result: resultState }).toMatchSnapshot(`defined type ${value}`);
    });
  });

  it('should handle all defined error types', () => {
    const specificTypes = [types.ADD_SOURCE, types.UPDATE_SOURCE];

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

      const resultState = addSourceWizardReducer(undefined, dispatched);

      expect({ type: helpers.REJECTED_ACTION(value), result: resultState }).toMatchSnapshot(`rejected types ${value}`);
    });
  });

  it('should handle all defined fulfilled types', () => {
    const specificTypes = [types.ADD_SOURCE, types.UPDATE_SOURCE, credentialsTypes.GET_WIZARD_CREDENTIALS];

    specificTypes.forEach(value => {
      const dispatched = {
        type: helpers.FULFILLED_ACTION(value),
        payload: {
          data: {
            test: 'success'
          }
        }
      };

      const resultState = addSourceWizardReducer(undefined, dispatched);

      expect({ type: helpers.FULFILLED_ACTION(value), result: resultState }).toMatchSnapshot(
        `fulfilled types ${value}`
      );
    });
  });
});
