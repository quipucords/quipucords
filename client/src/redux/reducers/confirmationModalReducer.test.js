import { confirmationModalTypes } from '../constants';
import confirmationModalReducer from './confirmationModalReducer';

describe('ConfirmationModalReducer', function() {
  it('should return the initial state', () => {
    const initialState = {
      show: false,
      confirmTitle: 'Confirm',
      confirmHeading: null,
      confirmBody: null,
      confirmButtonText: 'Confirm'
    };

    expect(confirmationModalReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle CONFIRMATION_MODAL_SHOW', () => {
    const dispatched = {
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      confirmTitle: 'Confirm',
      confirmHeading: null,
      confirmBody: null,
      confirmButtonText: 'Confirm',
      cancelActionType: '',
      confirmActionType: ''
    };

    expect(confirmationModalReducer(undefined, dispatched).show).toEqual(true);
  });

  it('should handle CONFIRMATION_MODAL_HIDE', () => {
    const dispatchShow = {
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW
    };

    const dispatchHide = {
      type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
    };

    expect(confirmationModalReducer(undefined, dispatchShow).show).toEqual(
      true
    );
    expect(confirmationModalReducer(undefined, dispatchHide).show).toEqual(
      false
    );
  });
});
