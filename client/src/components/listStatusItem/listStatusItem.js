import React from 'react';
import PropTypes from 'prop-types';
import cx from 'classnames';
import { Icon, ListView } from 'patternfly-react';
import _ from 'lodash';
import SimpleTooltip from '../simpleTooltIp/simpleTooltip';
import helpers from '../../common/helpers';

const ListStatusItem = ({
  id,
  count,
  emptyText,
  tipSingular,
  tipPlural,
  expanded,
  expandType,
  toggleExpand,
  iconInfo
}) => {
  const renderExpandContent = (displayIconInfo, displayCount, text) => {
    if (displayIconInfo) {
      const classes = cx('list-view-compound-item-icon', ..._.get(displayIconInfo, 'classNames', []));
      return (
        <React.Fragment>
          <Icon className={classes} type={displayIconInfo.type} name={displayIconInfo.name} />
          <strong>{displayCount}</strong>
        </React.Fragment>
      );
    }

    return (
      <span>
        <strong>{displayCount}</strong>
        {` ${text}`}
      </span>
    );
  };

  if (count > 0) {
    return (
      <ListView.InfoItem className="list-view-info-item-icon-count">
        <SimpleTooltip id={`${id}_tip`} tooltip={`${count}  ${count === 1 ? tipSingular : tipPlural}`}>
          <ListView.Expand
            expanded={expanded}
            toggleExpanded={() => {
              toggleExpand(expandType);
            }}
          >
            {renderExpandContent(iconInfo, count, tipPlural)}
          </ListView.Expand>
        </SimpleTooltip>
      </ListView.InfoItem>
    );
  }

  return (
    <ListView.InfoItem className="list-view-info-item-icon-count empty-count">
      <SimpleTooltip id={`${id}_tip`} tooltip={`0 ${tipPlural}`}>
        <span>{emptyText}</span>
      </SimpleTooltip>
    </ListView.InfoItem>
  );
};

ListStatusItem.propTypes = {
  id: PropTypes.string,
  count: PropTypes.number,
  emptyText: PropTypes.string,
  tipSingular: PropTypes.string,
  tipPlural: PropTypes.string,
  expanded: PropTypes.bool,
  expandType: PropTypes.string,
  toggleExpand: PropTypes.func,
  iconInfo: PropTypes.object
};

ListStatusItem.defaultProps = {
  id: null,
  count: 0,
  emptyText: null,
  tipSingular: null,
  tipPlural: null,
  expanded: false,
  expandType: null,
  toggleExpand: helpers.noop,
  iconInfo: null
};

export { ListStatusItem as default, ListStatusItem };
