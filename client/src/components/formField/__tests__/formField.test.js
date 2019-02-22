import React from 'react';
import { mount } from 'enzyme';
import { FormField, fieldValidation } from '../formField';

describe('FormField Component', () => {
  it('should render', () => {
    const props = { id: 'test' };

    const component = mount(
      <FormField {...props}>
        <input id="test" type="text" value="" readOnly />
      </FormField>
    );

    expect(component.render()).toMatchSnapshot();
    expect(
      component
        .find('label')
        .at(0)
        .render()
    ).toMatchSnapshot();
  });

  it('should have isEmpty validation', () => {
    expect(fieldValidation.isEmpty('')).toEqual(true);
    expect(fieldValidation.isEmpty('test')).toEqual(false);
  });

  it('should have doesntHaveMinimumCharacters validation', () => {
    expect(fieldValidation.doesntHaveMinimumCharacters('', 5)).toEqual(true);
    expect(fieldValidation.doesntHaveMinimumCharacters('test test', 5)).toEqual(false);
  });
});
