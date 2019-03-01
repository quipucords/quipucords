import React from 'react';
import { mount } from 'enzyme';
import { FormField, fieldValidation } from '../formField';

describe('FormField Component', () => {
  it('should render a basic component', () => {
    const props = { id: 'test' };

    const component = mount(
      <FormField {...props}>
        <input id="test" type="text" value="" readOnly />
      </FormField>
    );

    expect(component.render()).toMatchSnapshot('basic formfield');
    expect(
      component
        .find('label')
        .at(0)
        .render()
    ).toMatchSnapshot('basic label');
  });

  it('should handle multiple error message types', () => {
    const props = {
      id: 'test',
      error: true,
      errorMessage: 'lorem ipsum'
    };

    let component = mount(
      <FormField {...props}>
        <input id="test" type="text" value="" readOnly />
      </FormField>
    );

    expect(component.render()).toMatchSnapshot('string error message');

    props.errorMessage = true;

    component = mount(
      <FormField {...props}>
        <input id="test" type="text" value="" readOnly />
      </FormField>
    );

    expect(component.render()).toMatchSnapshot('boolean error message');

    props.errorMessage = <span>lorem ipsum</span>;

    component = mount(
      <FormField {...props}>
        <input id="test" type="text" value="" readOnly />
      </FormField>
    );

    expect(component.render()).toMatchSnapshot('node error message');
  });

  it('should have isEmpty validation', () => {
    expect(fieldValidation.isEmpty(undefined)).toBe(true);
    expect(fieldValidation.isEmpty(null)).toBe(true);
    expect(fieldValidation.isEmpty('')).toBe(true);
    expect(fieldValidation.isEmpty('lorem')).toBe(false);
    expect(fieldValidation.isEmpty([])).toBe(true);
    expect(fieldValidation.isEmpty(['lorem'])).toBe(false);
    expect(fieldValidation.isEmpty({})).toBe(true);
    expect(fieldValidation.isEmpty({ lorem: 'ipsum' })).toBe(false);
  });

  it('should have doesntHaveMinimumCharacters validation', () => {
    expect(fieldValidation.doesntHaveMinimumCharacters('', 5)).toBe(true);
    expect(fieldValidation.doesntHaveMinimumCharacters('test test', 5)).toBe(false);
  });

  it('should have isPortValid validation', () => {
    expect(fieldValidation.isPortValid('lorem')).toBe(false);
    expect(fieldValidation.isPortValid(-1)).toBe(false);
    expect(fieldValidation.isPortValid(65536)).toBe(false);
    expect(fieldValidation.isPortValid('65536')).toBe(false);
    expect(fieldValidation.isPortValid(65535)).toBe(true);
  });
});
