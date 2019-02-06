import confirmationModalReducer from '../confirmationModalReducer';
import { confirmationModalTypes as types } from '../../constants';

describe('ConfirmationModalReducer', () => {
  it('should return the initial state', () => {
    expect(confirmationModalReducer.initialState).toBeDefined();
  });

  it('should handle specific defined types', () => {
    const specificTypes = [types.CONFIRMATION_MODAL_HIDE, types.CONFIRMATION_MODAL_SHOW];

    specificTypes.forEach(value => {
      const dispatched = {
        type: value
      };

      const resultState = confirmationModalReducer(undefined, dispatched);

      expect({ type: value, result: resultState }).toMatchSnapshot(`defined type ${value}`);
    });
  });
});
