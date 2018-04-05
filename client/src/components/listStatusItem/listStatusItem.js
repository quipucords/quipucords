import React from 'react';
import PropTypes from 'prop-types';
import cx from 'classnames';
import { Icon, ListView } from 'patternfly-react';
import _ from 'lodash';
import SimpleTooltip from '../simpleTooltIp/simpleTooltip';

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
  let renderExpandContent = (iconInfo, count, text) => {
    if (iconInfo) {
      const classes = _.get(iconInfo.classNames, 'length', 0)
        ? cx('list-view-compound-item-icon', ...iconInfo.classNames)
        : 'list-view-compound-item-icon';
      return (
        <React.Fragment>
          <Icon className={classes} type={iconInfo.type} name={iconInfo.name} />
          <strong>{count}</strong>
        </React.Fragment>
      );
    } else {
      return (
        <span>
          <strong>{count}</strong>
          {` ${text}`}
        </span>
      );
    }
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

export default ListStatusItem;
